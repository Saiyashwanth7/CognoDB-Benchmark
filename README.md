# CognoDB Cloud vs. Managed Graph Databases — Benchmark Report

## 1. Summary

This benchmark compares **CognoDB Cloud** against four other graph database
platforms — **Neo4j AuraDB, Memgraph Cloud, FalkorDB, and self-hosted Neo4j
Community** — on identical data, identical queries, and matched resource
limits, to produce a fair, reproducible performance comparison.

_(Fill in a 3-4 sentence summary of your key finding once you have results.)_

## 2. Methodology

### 2.1 Platforms compared and why

| Platform                      | Why chosen                                                                                                                                                        | Resource tier used                           |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| CognoDB Cloud                 | Subject of the assignment                                                                                                                                         | Free (c0): 0.5 vCPU, 256MB RAM, 1GB disk     |
| Neo4j AuraDB                  | Same query language (Cypher) as CognoDB — isolates "is this a CognoDB-specific difference or a Cypher-engine-in-general difference"                               | Free tier — _(fill in exact specs)_          |
| Memgraph Cloud                | In-memory Cypher-compatible graph DB — tests whether in-memory architecture gives a real edge                                                                     | Free tier — _(fill in exact specs)_          |
| FalkorDB                      | Redis-based graph database — genuinely different underlying architecture (in-memory, Redis protocol) from the Neo4j-family engines, while still Cypher-compatible | Docker, capped to `--cpus=0.5 --memory=256m` |
| Neo4j Community (self-hosted) | Same engine family as AuraDB, but self-hosted — isolates "managed cloud overhead" vs "raw engine performance"                                                     | Docker, capped to `--cpus=0.5 --memory=256m` |

**Note on query language:** all five platforms are Cypher-compatible, so the
_same_ Cypher queries run against every platform unchanged (see
`benchmarks/run_benchmarks.py`). This was a deliberate choice: it removes
query-language differences as a variable, so any performance differences
observed can be attributed to the underlying engine/architecture, not to
subtle semantic differences between query languages.

### 2.2 Dataset

### 2.2 Dataset

- **Type:** Synthetic scale-free social graph (preferential attachment / Barabási–Albert style), generated via `data/prepare_dataset.py`. A real SNAP dataset was not used for this run — stated honestly per the assignment's methodology guidance.
- **Size:** 150,000 relationships across 75,058 nodes.
- **Generation method:** Preferential attachment — new nodes connect preferentially to already well-connected nodes, mimicking real social-network structure (a small number of high-degree hub nodes, many low-degree nodes), which is what makes the multi-hop traversal benchmarks meaningful.

### 2.3 Fairness — resource parity

All platforms were constrained to **0.5 vCPU / 256MB RAM / 1GB disk**, matching
CognoDB's free tier, per the assignment's fairness requirement. Docker-hosted
platforms (FalkorDB, self-hosted Neo4j) were capped explicitly via `--cpus`
and `--memory` flags; cloud free tiers (CognoDB, Neo4j AuraDB, Memgraph Cloud)
were used as-is and their advertised specs are recorded above.

### 2.4 Load method

Batched `UNWIND` inserts (batch size: 1000 rows/query) via the Neo4j Python
driver — see `loaders/load_cypher.py`. One-row-at-a-time inserts were avoided
as they don't reflect realistic bulk-load practice.

### 2.5 Query workload

All five platforms ran the **identical Cypher queries** — see
`benchmarks/run_benchmarks.py`. No query-language translation was needed
since every platform in this comparison speaks Cypher.

### 2.6 Warm-up and measurement

10 warm-up iterations (discarded) followed by 100 measured iterations per
read workload, per the assignment's minimum. p50 and p95 latencies reported
for every metric.

## 3. Results

### 3.1 Data loading

### 3.1 Data loading

| Platform          | Nodes  | Relationships | Wall-clock (s) | Nodes/sec | Rels/sec |
| ----------------- | ------ | ------------- | -------------- | --------- | -------- |
| CognoDB           | 75,058 | 150,000       | 242.324        | 309.7     | 619.0    |
| Neo4j AuraDB      | 75,058 | 150,000       | 127.368        | 589.3     | 1,177.7  |
| Memgraph Cloud    | 75,058 | 150,000       | 215.093        | 349.0     | 697.4    |
| FalkorDB          | 75,058 | 150,000       | 18.788         | 3,995.0   | 7,983.9  |
| Neo4j Self-hosted | 75,058 | 150,000       | 91.65          | 819.0     | 1,636.7  |

### 3.2 Traversal latency (ms)

| Platform          | 1-hop p50 | 1-hop p95 | 2-hop p50 | 2-hop p95 | 3-hop p50 | 3-hop p95 |
| ----------------- | --------- | --------- | --------- | --------- | --------- | --------- |
| CognoDB           | 960.524   | 1189.737  | 960.458   | 1121.688  | 959.588   | 1121.673  |
| Neo4j AuraDB      | 218.634   | 388.64    | 217.001   | 435.66    | 217.21    | 347.394   |
| Memgraph Cloud    | 960.186   | 1121.843  | 960.115   | 1119.406  | 960.25    | 1119.006  |
| FalkorDB          | 0.556     | 0.815     | 1.103     | 1.586     | 1.121     | 2.007     |
| Neo4j Self-hosted | 11.991    | 75.134    | 16.016    | 92.508    | 13.995    | 42.295    |

### 3.3 Lookups (ms)

| Platform          | Point lookup p50 | Point lookup p95 |
| ----------------- | ---------------- | ---------------- |
| CognoDB           | 959.99           | 1119.068         |
| Neo4j AuraDB      | 223.235          | 865.934          |
| Memgraph Cloud    | 960.495          | 1120.286         |
| FalkorDB          | 0.486            | 1.055            |
| Neo4j Self-hosted | 7.721            | 65.151           |

| Platform          | Point lookup p50 | Point lookup p95 | Indexed lookup p50 | Indexed lookup p95 | Indexed property |
| ----------------- | ---------------- | ---------------- | ------------------ | ------------------ | ---------------- |
| CognoDB           |                  |                  |                    |                    | id               |
| Neo4j AuraDB      |                  |                  |                    |                    | id               |
| Memgraph Cloud    |                  |                  |                    |                    | id               |
| FalkorDB          |                  |                  |                    |                    | id               |
| Neo4j Self-hosted |                  |                  |                    |                    | id               |

### 3.4 Aggregation (ms)

| Platform          | p50      | p95      |
| ----------------- | -------- | -------- |
| CognoDB           | 2079.47  | 2169.36  |
| Neo4j AuraDB      | 300.739  | 801.019  |
| Memgraph Cloud    | 1110.451 | 1881.899 |
| FalkorDB          | 209.143  | 262.171  |
| Neo4j Self-hosted | 200.524  | 2103.868 |

### 3.5 Mixed concurrent workload

Config: 10 concurrent clients, 15 second duration, 80% read / 20% write.

### 3.5 Mixed concurrent workload

Config: 10 concurrent clients, 15 second duration, 80% read / 20% write.

| Platform          | Total ops | Errors | Error rate | Throughput (qps) |
| ----------------- | --------- | ------ | ---------- | ---------------- |
| CognoDB           | 116       | 29     | 20.0%      | 7.73             |
| Neo4j AuraDB      | 444       | 0      | 0%         | 29.6             |
| Memgraph Cloud    | 152       | 0      | 0%         | 10.13            |
| FalkorDB          | 22,612    | 0      | 0%         | 1,507.47         |
| Neo4j Self-hosted | 40        | 0      | 0%         | 2.67             |

CognoDB under concurrency showed a 20% error rate (29 of 145 total attempted operations failed with a driver-level protocol violation — the same failure mode observed during bulk loading), reducing effective throughput to 7.73 qps. This reinforces the loading-phase finding: CognoDB's free tier appears to intermittently return malformed responses, and this gets measurably worse under concurrent load rather than being a one-off fluke.

Neo4j Self-hosted, despite the lowest single-query latencies of any disk-backed platform (7–16ms, see 3.2/3.3), had the second-worst concurrent throughput of the whole comparison at 2.67 qps — slower even than CognoDB's degraded number. The likely cause is visible in the resource footprint data (3.6): the container was already running at 98.13% of its 256MB memory limit at rest, before any concurrent load was applied. Ten simultaneous clients against a JVM-based engine with almost no memory headroom likely triggered heavy GC pressure or page-cache thrashing — a case where per-query speed and concurrent throughput tell very different stories, and where the fairness-driven 256MB cap (matching CognoDB's tier) may be genuinely under-provisioned for Neo4j's JVM overhead specifically, versus FalkorDB's leaner memory profile at the same limit (3.6: 48.96% usage).

### 3.6 Resource footprint

| Platform          | Stored data size                                            | Memory usage                         | Notes                                                      |
| ----------------- | ----------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------- |
| CognoDB           | Not observable via free-tier console                        | Not observable via free-tier console |                                                            |
| Neo4j AuraDB      | Not observable via free-tier console                        | Not observable via free-tier console |                                                            |
| Memgraph Cloud    | Not observable via free-tier console                        | Not observable via free-tier console |                                                            |
| FalkorDB          | Not directly exposed (in-memory, no separate on-disk store) | 125.3 MiB / 256 MiB (48.96%)         | Comfortable headroom at this dataset size                  |
| Neo4j Self-hosted | Not captured separately (see note)                          | 251.2 MiB / 256 MiB (98.13%)         | Running at the edge of its memory limit — see caveat below |

## 4. Analysis

_(Write 3-5 paragraphs once you have real numbers: which platform was
fastest at what, and your best-reasoned explanation why — e.g. in-memory vs
disk-backed, managed-cloud network overhead vs local Docker, index usage
differences, etc.)_

## 5. Caveats and honest limitations

- _(e.g. "Free-tier CognoDB showed occasional latency spikes under
  concurrent load, possibly due to shared-tenant throttling — see raw logs
  in results/")_
- _(e.g. "Docker-hosted platforms run on local hardware while cloud platforms
  incur network round-trip latency to their respective regions — this is a
  genuine confound worth naming honestly rather than hiding")_
- _(List anything that went wrong, timed out, or required a workaround —
  the assignment explicitly rewards honesty here.)_

## 6. Reproducing this benchmark

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your own credentials

# Start Docker-hosted platforms:
docker run -d -p 6379:6379 --cpus=0.5 --memory=256m --name falkordb-benchmark falkordb/falkordb
docker run -d -p 7688:7687 -p 7475:7474 --cpus=0.5 --memory=256m --name neo4j-selfhosted -e NEO4J_AUTH=neo4j/password123 neo4j:community

# Generate the shared dataset:
python data/prepare_dataset.py

# Load into every platform:
python loaders/load_cypher.py cognodb
python loaders/load_cypher.py neo4j_aura
python loaders/load_cypher.py memgraph
python loaders/load_cypher.py falkordb
python loaders/load_cypher.py neo4j_selfhosted

# Run benchmarks against every platform:
python benchmarks/run_benchmarks.py cognodb
python benchmarks/run_benchmarks.py neo4j_aura
python benchmarks/run_benchmarks.py memgraph
python benchmarks/run_benchmarks.py falkordb
python benchmarks/run_benchmarks.py neo4j_selfhosted
```
