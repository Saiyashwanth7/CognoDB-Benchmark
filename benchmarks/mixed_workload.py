"""
Mixed concurrent read/write workload.

WHY THIS MATTERS: single-query latency (what run_benchmarks.py measures)
tells you how fast ONE query is. It doesn't tell you what happens when many
clients hit the database AT THE SAME TIME — which is what a real production
system actually looks like. This script simulates N concurrent clients, each
firing a mix of reads and writes, and measures total sustained throughput
(queries/second), which is what "concurrent read/write throughput" in the
assignment is asking for.

We use a ThreadPoolExecutor because the Neo4j Python driver releases the GIL
during network I/O (waiting on the database), so threads genuinely run
concurrently for this kind of workload — no need for multiprocessing.
"""

import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read_op(client, sample_ids):
    node_id = random.choice(sample_ids)
    client.run_read("MATCH (p:Person {id: $id}) RETURN p", id=node_id)


def write_op(client, sample_ids):
    # A lightweight write that doesn't grow the dataset unboundedly during the test:
    # updates a property instead of creating new nodes/relationships.
    node_id = random.choice(sample_ids)
    client.run_write(
        "MATCH (p:Person {id: $id}) SET p.last_touched = timestamp()", id=node_id
    )


def run_mixed_workload(
    client, sample_ids, num_clients=10, duration_seconds=15, write_ratio=0.2
):
    """
    write_ratio=0.2 means ~20% writes, 80% reads — a reasonable default mix
    for a social-graph-style read-heavy workload. Document this ratio in
    your README since the assignment requires stating the read/write mix.
    """
    stop_time = time.time() + duration_seconds
    completed_ops = [0]  # mutable container so threads can increment it

    def worker():
        count = 0
        errors = 0
        while time.time() < stop_time:
            try:
                if random.random() < write_ratio:
                    write_op(client, sample_ids)
                else:
                    read_op(client, sample_ids)
                count += 1
            except Exception:
                errors += 1
        return count, errors

    with ThreadPoolExecutor(max_workers=num_clients) as executor:
        futures = [executor.submit(worker) for _ in range(num_clients)]
        op_results = [f.result() for f in as_completed(futures)]

    total_ops = sum(r[0] for r in op_results)
    total_errors = sum(r[1] for r in op_results)

    return {
        "num_clients": num_clients,
        "duration_seconds": duration_seconds,
        "write_ratio": write_ratio,
        "total_operations": total_ops,
        "total_errors": total_errors,
        "throughput_qps": round(total_ops / duration_seconds, 2),
        "error_rate": (
            round(total_errors / (total_ops + total_errors), 4)
            if (total_ops + total_errors) > 0
            else 0
        ),
    }


if __name__ == "__main__":
    import argparse
    import json
    from config import PLATFORMS
    from common.db_client import get_client
    from run_benchmarks import get_sample_node_ids

    parser = argparse.ArgumentParser()
    parser.add_argument("platform")
    parser.add_argument("--clients", type=int, default=10)
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--write-ratio", type=float, default=0.2)
    args = parser.parse_args()

    cfg = PLATFORMS[args.platform]
    client = get_client(cfg)

    print(f"Fetching sample node ids from {args.platform}...")
    sample_ids = get_sample_node_ids(client, n=30)

    print(
        f"Running mixed workload on {args.platform}: "
        f"{args.clients} clients, {args.duration}s, "
        f"{int(args.write_ratio * 100)}% writes..."
    )
    results = run_mixed_workload(
        client,
        sample_ids,
        num_clients=args.clients,
        duration_seconds=args.duration,
        write_ratio=args.write_ratio,
    )
    results["platform"] = args.platform
    client.close()

    out_path = f"results/{args.platform}_mixed_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {out_path}")
    print(json.dumps(results, indent=2))
