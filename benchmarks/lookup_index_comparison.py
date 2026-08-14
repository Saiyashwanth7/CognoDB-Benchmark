"""
Compares point-lookup latency WITHOUT an index vs WITH an index, on the
same query, same data, same platform. We do this by temporarily dropping
the existing Person.id index, measuring, then recreating it — this avoids
a full reload (data doesn't change, only the index does).

Run AFTER loaders/load_cypher.py has already loaded data for this platform.
"""

import time
import sys
import os
import json
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PLATFORMS, BENCHMARK_CONFIG
from common.db_client import get_client
from run_benchmarks import get_sample_node_ids, time_query, percentiles


def drop_index(client, platform_name):
    """Platform-specific index removal. Best-effort — some platforms may
    not support dropping a not-yet-named or already-created index cleanly,
    so failures here are caught and reported rather than crashing the run."""
    try:
        if platform_name == "falkordb":
            client.run_write("DROP INDEX ON :Person(id)")
        elif platform_name == "memgraph":
            client.run_auto("DROP INDEX ON :Person(id)")
        else:
            # Neo4j-family: CognoDB, Neo4j AuraDB, Neo4j Self-hosted
            client.run_write("DROP INDEX person_id_index IF EXISTS")
        return True
    except Exception as e:
        print(f"  WARNING: could not drop index on {platform_name}: {e}")
        return False


def create_index(client, platform_name):
    """Mirrors loaders/load_cypher.py's per-platform index creation."""
    if platform_name == "falkordb":
        try:
            client.run_write("CREATE INDEX FOR (p:Person) ON (p.id)")
        except Exception as e:
            if (
                "already indexed" in str(e).lower()
                or "already exists" in str(e).lower()
            ):
                pass
            else:
                raise
    elif platform_name == "memgraph":
        client.run_auto("CREATE INDEX FOR (p:Person) ON (p.id)")
    else:
        client.run_write(
            "CREATE INDEX person_id_index IF NOT EXISTS FOR (p:Person) ON (p.id)"
        )


def benchmark_point_lookup(client, sample_ids, warmup, iterations):
    cypher = "MATCH (p:Person {id: $id}) RETURN p"
    for i in range(warmup):
        client.run_read(cypher, id=sample_ids[i % len(sample_ids)])
    latencies = []
    for i in range(iterations):
        node_id = sample_ids[i % len(sample_ids)]
        latencies.append(time_query(client.run_read, cypher, id=node_id))
    return percentiles(latencies)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("platform")
    args = parser.parse_args()

    cfg = PLATFORMS[args.platform]
    client = get_client(cfg)
    bcfg = BENCHMARK_CONFIG

    print(f"Fetching sample node ids from {args.platform}...")
    sample_ids = get_sample_node_ids(client, n=30)

    print(f"Dropping index on {args.platform}...")
    dropped = drop_index(client, args.platform)

    results = {"platform": args.platform}

    if dropped:
        print("Measuring UNINDEXED point lookup...")
        results["unindexed_lookup"] = benchmark_point_lookup(
            client, sample_ids, bcfg["warmup_iterations"], bcfg["measured_iterations"]
        )
    else:
        results["unindexed_lookup"] = None
        print("Skipping unindexed measurement — index could not be dropped.")

    print(f"Recreating index on {args.platform}...")
    create_index(client, args.platform)

    print("Measuring INDEXED point lookup...")
    results["indexed_lookup"] = benchmark_point_lookup(
        client, sample_ids, bcfg["warmup_iterations"], bcfg["measured_iterations"]
    )

    client.close()

    out_path = f"results/{args.platform}_lookup_comparison.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {out_path}")
    print(json.dumps(results, indent=2))
