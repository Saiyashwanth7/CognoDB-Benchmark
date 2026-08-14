"""
Run this AFTER you've run benchmarks.run_benchmarks on all 5 platforms.

It reads every results/<platform>_results.json file and prints out ready-to-paste
markdown tables — comparing all 5 platforms side by side. Copy the output
straight into your README's Section 3 (Results), replacing the empty tables.
"""

import json
import os

PLATFORM_ORDER = ["cognodb", "neo4j_aura", "memgraph", "falkordb", "neo4j_selfhosted"]
PLATFORM_LABELS = {
    "cognodb": "CognoDB",
    "neo4j_aura": "Neo4j AuraDB",
    "memgraph": "Memgraph Cloud",
    "falkordb": "FalkorDB",
    "neo4j_selfhosted": "Neo4j Self-hosted",
}


def load_all_results():
    results = {}
    for platform in PLATFORM_ORDER:
        path = f"results/{platform}_results.json"
        if os.path.exists(path):
            with open(path) as f:
                results[platform] = json.load(f)
        else:
            print(
                f"WARNING: {path} not found — skipping {platform} (run its benchmark first)"
            )
    return results


def print_traversal_table(results):
    print("\n### 3.2 Traversal latency (ms)\n")
    print(
        "| Platform | 1-hop p50 | 1-hop p95 | 2-hop p50 | 2-hop p95 | 3-hop p50 | 3-hop p95 |"
    )
    print("|---|---|---|---|---|---|---|")
    for platform in PLATFORM_ORDER:
        if platform not in results:
            continue
        r = results[platform]
        row = [PLATFORM_LABELS[platform]]
        for hop in [1, 2, 3]:
            key = f"{hop}hop_traversal"
            row.append(str(r[key]["p50_ms"]))
            row.append(str(r[key]["p95_ms"]))
        print("| " + " | ".join(row) + " |")


def print_lookup_table(results):
    print("\n### 3.3 Lookups (ms)\n")
    print("| Platform | Point lookup p50 | Point lookup p95 |")
    print("|---|---|---|")
    for platform in PLATFORM_ORDER:
        if platform not in results:
            continue
        r = results[platform]
        row = [
            PLATFORM_LABELS[platform],
            str(r["point_lookup"]["p50_ms"]),
            str(r["point_lookup"]["p95_ms"]),
        ]
        print("| " + " | ".join(row) + " |")


def print_aggregation_table(results):
    print("\n### 3.4 Aggregation (ms)\n")
    print("| Platform | p50 | p95 |")
    print("|---|---|---|")
    for platform in PLATFORM_ORDER:
        if platform not in results:
            continue
        r = results[platform]
        row = [
            PLATFORM_LABELS[platform],
            str(r["aggregation"]["p50_ms"]),
            str(r["aggregation"]["p95_ms"]),
        ]
        print("| " + " | ".join(row) + " |")


def print_ranking_summary(results):
    """Quick 'who won what' summary — useful for writing your Analysis section."""
    print("\n### Quick ranking summary (for writing your Analysis section)\n")
    metrics = [
        ("1hop_traversal", "1-hop traversal (p50)"),
        ("2hop_traversal", "2-hop traversal (p50)"),
        ("3hop_traversal", "3-hop traversal (p50)"),
        ("point_lookup", "Point lookup (p50)"),
        ("aggregation", "Aggregation (p50)"),
    ]
    for key, label in metrics:
        available = [
            (p, results[p][key]["p50_ms"]) for p in PLATFORM_ORDER if p in results
        ]
        if not available:
            continue
        fastest = min(available, key=lambda x: x[1])
        print(
            f"- Fastest at {label}: **{PLATFORM_LABELS[fastest[0]]}** ({fastest[1]}ms)"
        )


if __name__ == "__main__":
    results = load_all_results()
    if not results:
        print(
            "No results found yet — run benchmarks/run_benchmarks.py against each platform first."
        )
        exit(1)

    print(f"\nLoaded results for {len(results)}/5 platforms: {list(results.keys())}")
    print("\n" + "=" * 70)
    print("COPY THE TABLES BELOW INTO YOUR README (Section 3: Results)")
    print("=" * 70)

    print_traversal_table(results)
    print_lookup_table(results)
    print_aggregation_table(results)
    print_ranking_summary(results)
