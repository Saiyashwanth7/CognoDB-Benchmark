"""
Generic Cypher-based loader — works for ANY platform whose client understands
Cypher-style queries: CognoDB, Neo4j AuraDB, Memgraph (via BoltClient), AND
FalkorDB (via FalkorClient) — because FalkorDB also implements Cypher-style
querying (a subset of openCypher), even though its underlying protocol is
Redis, not Bolt.

This replaces load_bolt.py — same logic, but uses the get_client() factory
so it works across every Cypher-speaking platform in config.py, not just
the strictly-Bolt ones.
"""

import csv
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.db_client import get_client


def create_index(client, platform_name):
    """
    Index creation syntax and transaction-mode requirements differ by
    platform — handle each explicitly rather than assuming one Cypher
    dialect works everywhere.
    """
    if platform_name == "falkordb":
        # FalkorDB uses older, simpler index syntax — no name, no IF NOT EXISTS.
        # Wrap in try/except since re-running raises an error if it already
        # exists, unlike Neo4j's IF NOT EXISTS clause.
        try:
            client.run_write("CREATE INDEX FOR (p:Person) ON (p.id)")
        except Exception as e:
            if (
                "already indexed" in str(e).lower()
                or "already exists" in str(e).lower()
            ):
                print(f"  (index already exists on {platform_name}, continuing)")
            else:
                raise
    elif platform_name == "memgraph":
        # Memgraph rejects index creation inside an explicit transaction
        # ("multicommand transaction") — must run as an auto-committing
        # standalone statement instead.
        client.run_auto("CREATE INDEX FOR (p:Person) ON (p.id)")
    else:
        # Neo4j-family (CognoDB, Neo4j AuraDB, self-hosted Neo4j) supports the
        # newer named IF NOT EXISTS syntax.
        client.run_write(
            "CREATE INDEX person_id_index IF NOT EXISTS FOR (p:Person) ON (p.id)"
        )


def load_edges(client, csv_path, platform_name, batch_size=1000):
    create_index(client, platform_name)

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = [
            {"source": int(r["source_id"]), "target": int(r["target_id"])}
            for r in reader
        ]

    total_relationships = len(rows)
    total_nodes = len(set(r["source"] for r in rows) | set(r["target"] for r in rows))

    start = time.perf_counter()
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        client.run_write(
            """
            UNWIND $batch AS row
            MERGE (a:Person {id: row.source})
            MERGE (b:Person {id: row.target})
            MERGE (a)-[:FRIEND]->(b)
            RETURN count(*) AS processed
            """,
            batch=batch,
        )
        if i % (batch_size * 10) == 0:
            print(f"  ...loaded {i:,}/{total_relationships:,} relationships")
    elapsed = time.perf_counter() - start

    return {
        "total_nodes": total_nodes,
        "total_relationships": total_relationships,
        "wall_clock_seconds": round(elapsed, 3),
        "nodes_per_second": round(total_nodes / elapsed, 1),
        "relationships_per_second": round(total_relationships / elapsed, 1),
    }


if __name__ == "__main__":
    import argparse
    from config import PLATFORMS

    parser = argparse.ArgumentParser()
    parser.add_argument("platform", help="cognodb, neo4j_aura, memgraph, or falkordb")
    args = parser.parse_args()

    cfg = PLATFORMS[args.platform]
    client = get_client(cfg)
    print(f"Loading into {args.platform}...")
    stats = load_edges(client, "data/edges.csv", args.platform)
    print(f"[{args.platform}] Load stats: {stats}")
    client.close()
