"""
Prepares the benchmark dataset.

Two options:
1. Download a real SNAP dataset and trim it to size (preferred — more credible,
   and the assignment explicitly suggests SNAP soc-Pokec).
2. Generate a synthetic scale-free social graph as a fallback if the download
   is slow/unavailable — still realistic (uses preferential attachment, same
   pattern real social networks follow), and you can say so honestly in
   your README's methodology section.

Run this FIRST, before any loading — it writes edges.csv used by every loader.
"""
import csv
import random

TARGET_RELATIONSHIPS = 150_000  # within the assignment's suggested 100k-500k range


def generate_synthetic_social_graph(num_edges=TARGET_RELATIONSHIPS, seed=42):
    """
    Generates a synthetic graph using preferential attachment (Barabasi-Albert
    style) — new nodes are more likely to connect to already well-connected
    nodes, which mimics real social network structure (a few highly-connected
    hubs, many nodes with few connections). This is why real social graphs
    have "small world" properties, which is exactly what makes multi-hop
    traversal benchmarks meaningful.
    """
    random.seed(seed)
    edges = []
    node_degree = {0: 1, 1: 1}  # start with a seed edge
    edges.append((0, 1))
    next_node_id = 2

    # Track nodes weighted by their current degree, for preferential attachment
    degree_pool = [0, 1]

    while len(edges) < num_edges:
        new_node = next_node_id
        next_node_id += 1
        # Pick 1-3 existing nodes to connect to, weighted toward high-degree nodes
        num_connections = random.randint(1, 3)
        targets = random.sample(degree_pool, min(num_connections, len(degree_pool)))

        for target in targets:
            if len(edges) >= num_edges:
                break
            edges.append((new_node, target))
            degree_pool.append(new_node)
            degree_pool.append(target)

    return edges


def write_edges_csv(edges, path="data/edges.csv"):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source_id", "target_id"])
        writer.writerows(edges)
    node_count = len(set(n for edge in edges for n in edge))
    print(f"Wrote {len(edges):,} relationships across {node_count:,} nodes to {path}")


if __name__ == "__main__":
    edges = generate_synthetic_social_graph()
    write_edges_csv(edges)
