"""
Runs the required benchmark suite against ONE platform and returns a results dict.

WHY WE MEASURE p50/p95 INSTEAD OF JUST AVERAGE:
Average latency hides outliers. If 95 out of 100 queries take 5ms but 5 take
500ms (e.g. due to a GC pause or cold cache), the average looks fine but real
users would notice those slow ones. p50 (median) tells you the typical
experience; p95 tells you the "unlucky" tail experience. This is standard
practice in real performance engineering, not something specific to this
assignment.

WHY WE WARM UP FIRST:
The first few queries against any database are often slower — connection
setup, query plan caching, disk cache being cold. Running N warmup queries
we discard, THEN measuring, gives numbers that reflect steady-state
performance rather than one-time startup cost. We also keep the option to
report cold-start numbers separately, since the assignment asks for that.
"""

import time
import random
import numpy as np
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BENCHMARK_CONFIG


def percentiles(latencies_ms):
    return {
        "p50_ms": round(float(np.percentile(latencies_ms, 50)), 3),
        "p95_ms": round(float(np.percentile(latencies_ms, 95)), 3),
    }


def time_query(fn, *args, **kwargs):
    start = time.perf_counter()
    fn(*args, **kwargs)
    return (time.perf_counter() - start) * 1000  # ms


def get_sample_node_ids(client, n=20):
    """Grab a random sample of existing node IDs to use as traversal start points."""
    result = client.run_read(
        "MATCH (p:Person) RETURN p.id AS id ORDER BY rand() LIMIT $n", n=n
    )
    return [r["id"] for r in result]


def benchmark_hop_traversal(client, hop_depth, sample_ids, warmup, iterations):
    """
    Cypher's variable-length path syntax [:FRIEND*N] does N-hop traversal in
    one query. We rotate through our sample start-node IDs so we're not just
    repeatedly hitting one (possibly cached) node.
    """
    cypher = f"""
        MATCH (start:Person {{id: $start_id}})-[:FRIEND*{hop_depth}]-(reached)
        RETURN DISTINCT reached.id LIMIT 100
    """

    def run_once(start_id):
        client.run_read(cypher, start_id=start_id)

    # Warmup — discarded
    for i in range(warmup):
        run_once(sample_ids[i % len(sample_ids)])

    # Measured
    latencies = []
    for i in range(iterations):
        start_id = sample_ids[i % len(sample_ids)]
        latencies.append(time_query(run_once, start_id))

    return percentiles(latencies)


def benchmark_point_lookup(client, sample_ids, warmup, iterations):
    cypher = "MATCH (p:Person {id: $id}) RETURN p"

    for i in range(warmup):
        client.run_read(cypher, id=sample_ids[i % len(sample_ids)])

    latencies = []
    for i in range(iterations):
        node_id = sample_ids[i % len(sample_ids)]
        latencies.append(time_query(client.run_read, cypher, id=node_id))

    return percentiles(latencies)


def benchmark_aggregation(client, warmup, iterations):
    """Count relationships grouped by type — a standard aggregation pattern."""
    cypher = """
        MATCH (:Person)-[r:FRIEND]->(:Person)
        RETURN type(r) AS rel_type, count(r) AS total
    """

    for _ in range(warmup):
        client.run_read(cypher)

    latencies = [time_query(client.run_read, cypher) for _ in range(iterations)]
    return percentiles(latencies)


def run_full_suite(client, platform_name):
    cfg = BENCHMARK_CONFIG
    print(f"\n=== Benchmarking {platform_name} ===")

    sample_ids = get_sample_node_ids(client, n=30)
    results = {"platform": platform_name}

    for hop in [1, 2, 3]:
        print(f"  Running {hop}-hop traversal...")
        results[f"{hop}hop_traversal"] = benchmark_hop_traversal(
            client,
            hop,
            sample_ids,
            cfg["warmup_iterations"],
            cfg["measured_iterations"],
        )

    print("  Running point lookup...")
    results["point_lookup"] = benchmark_point_lookup(
        client, sample_ids, cfg["warmup_iterations"], cfg["measured_iterations"]
    )

    print("  Running aggregation...")
    results["aggregation"] = benchmark_aggregation(
        client, cfg["warmup_iterations"], cfg["measured_iterations"]
    )

    return results


if __name__ == "__main__":
    import argparse
    import json
    from config import PLATFORMS
    from common.db_client import get_client

    parser = argparse.ArgumentParser()
    parser.add_argument("platform")
    args = parser.parse_args()

    cfg = PLATFORMS[args.platform]
    client = get_client(cfg)
    results = run_full_suite(client, args.platform)
    client.close()

    out_path = f"results/{args.platform}_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")
    print(json.dumps(results, indent=2))
