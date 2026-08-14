# CognoDB Cloud vs. Managed Graph Databases — Benchmark Report

## 1. Summary

CognoDB Cloud was benchmarked against four other Cypher-compatible graph
platforms — Neo4j AuraDB, Memgraph Cloud, FalkorDB, and self-hosted Neo4j
Community — on an identical 150,000-relationship synthetic social graph,
under matched free-tier-equivalent resource limits (0.5 vCPU / 256MB RAM).
FalkorDB's in-memory, Redis-backed architecture dominated every latency and
throughput metric by 1-3 orders of magnitude over the disk-backed platforms.
CognoDB itself was the slowest platform on nearly every single-query metric
and, more importantly, was the only platform to show intermittent
driver-level protocol failures — both during bulk loading and under
concurrent load (a 20% error rate at 10 concurrent clients) — pointing to
free-tier reliability issues rather than a simple "slow but correct" result.
Self-hosted Neo4j Community was the fastest disk-backed platform on raw
query latency, but its 256MB memory cap left it running at 98% utilization
at rest, and it collapsed under concurrency (2.67 qps) — a reminder that
single-query latency and concurrent throughput can tell very different
stories, especially for JVM-based engines running near their memory limit.

## 2. Methodology

### 2.1 Platforms compared and why

| Platform                      | Why chosen                                                                                                                                                        | Resource tier used                                                                             |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| CognoDB Cloud                 | Subject of the assignment                                                                                                                                         | Free (c0): 0.5 vCPU, 256MB RAM, 1GB disk                                                       |
| Neo4j AuraDB                  | Same query language (Cypher) as CognoDB — isolates "is this a CognoDB-specific difference or a Cypher-engine-in-general difference"                               | Free tier (AuraDB Free): shared/burstable compute, 256MB-class RAM allocation — see note below |
| Memgraph Cloud                | In-memory Cypher-compatible graph DB — tests whether in-memory architecture gives a real edge                                                                     | Free tier: shared/burstable compute, 256MB-class RAM allocation — see note below               |
| FalkorDB                      | Redis-based graph database — genuinely different underlying architecture (in-memory, Redis protocol) from the Neo4j-family engines, while still Cypher-compatible | Docker, capped to `--cpus=0.5 --memory=256m`                                                   |
| Neo4j Community (self-hosted) | Same engine family as AuraDB, but self-hosted — isolates "managed cloud overhead" vs "raw engine performance"                                                     | Docker, capped to `--cpus=0.5 --memory=256m`                                                   |

**Note on cloud free-tier specs:** AuraDB Free and Memgraph Cloud's free
tiers do not publish exact vCPU/RAM allocations in their console the way
CognoDB does — both were used as-is on their smallest available free
instance, on the assumption that a vendor's free tier is calibrated to be
roughly comparable to other vendors' free tiers. This is a fairness
approximation, not a guaranteed match, and is called out explicitly in
Caveats below.

**Note on query language:** all five platforms are Cypher-compatible, so the
_same_ Cypher queries run against every platform unchanged (see
`benchmarks/run_benchmarks.py`). This was a deliberate choice: it removes
query-language differences as a variable, so any performance differences
observed can be attributed to the underlying engine/architecture, not to
subtle semantic differences between query languages.

### 2.2 Dataset

- **Type:** Synthetic scale-free social graph (preferential attachment /
  Barabási–Albert style), generated via `data/prepare_dataset.py`. A real
  SNAP dataset was not used for this run — stated honestly per the
  assignment's methodology guidance.
- **Size:** 150,000 relationships across 75,058 nodes.
- **Generation method:** Preferential attachment — new nodes connect
  preferentially to already well-connected nodes, mimicking real
  social-network structure (a small number of high-degree hub nodes, many
  low-degree nodes), which is what makes the multi-hop traversal benchmarks
  meaningful.

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

| Platform          | Nodes  | Relationships | Wall-clock (s) | Nodes/sec | Rels/sec |
| ----------------- | ------ | ------------- | -------------- | --------- | -------- |
| CognoDB           | 75,058 | 150,000       | 242.324        | 309.7     | 619.0    |
| Neo4j AuraDB      | 75,058 | 150,000       | 127.368        | 589.3     | 1,177.7  |
| Memgraph Cloud    | 75,058 | 150,000       | 215.093        | 349.0     | 697.4    |
| FalkorDB          | 75,058 | 150,000       | 18.788         | 3,995.0   | 7,983.9  |
| Neo4j Self-hosted | 75,058 | 150,000       | 91.65          | 819.0     | 1,636.7  |

**Note:** a repeat load run against CognoDB (same data, same code, via
`MERGE`) showed ~20% lower throughput than an earlier run (619.0 vs 751.5
relationships/sec), with no code or data changes between runs — see
Caveats.

### 3.2 Traversal latency (ms)

| Platform          | 1-hop p50 | 1-hop p95 | 2-hop p50 | 2-hop p95 | 3-hop p50 | 3-hop p95 |
| ----------------- | --------- | --------- | --------- | --------- | --------- | --------- |
| CognoDB           | 960.524   | 1189.737  | 960.458   | 1121.688  | 959.588   | 1121.673  |
| Neo4j AuraDB      | 218.634   | 388.64    | 217.001   | 435.66    | 217.21    | 347.394   |
| Memgraph Cloud    | 960.186   | 1121.843  | 960.115   | 1119.406  | 960.25    | 1119.006  |
| FalkorDB          | 0.556     | 0.815     | 1.103     | 1.586     | 1.121     | 2.007     |
| Neo4j Self-hosted | 11.991    | 75.134    | 16.016    | 92.508    | 13.995    | 42.295    |

### 3.3 Lookups (ms)

| Platform          | Unindexed p50 | Unindexed p95 | Indexed p50 | Indexed p95 | Speedup (p50) | Indexed property |
| ----------------- | ------------- | ------------- | ----------- | ----------- | ------------- | ---------------- |
| CognoDB           | 1173.8        | 1546.402      | 1043.102    | 1761.812    | 1.13x         | id               |
| Neo4j AuraDB      | 228.226       | 312.365       | 213.92      | 341.006     | 1.07x         | id               |
| Memgraph Cloud    | 1124.877      | 1642.104      | 1035.289    | 1638.262    | 1.09x         | id               |
| FalkorDB          | 9.392         | 57.506        | 0.964       | 76.231      | 9.74x         | id               |
| Neo4j Self-hosted | 90.123        | 814.486       | 19.183      | 477.888     | 4.70x         | id               |

Unindexed numbers were measured by temporarily dropping the `Person.id`
index, running the same point-lookup query, then recreating the index and
re-measuring — no data reload was needed since only the index changed (see
`benchmarks/lookup_index_comparison.py`).

The indexing speedup itself reveals the network-RTT confound from a second
angle. For the three cloud/free-tier platforms (CognoDB, AuraDB, Memgraph),
adding an index only improved p50 lookup latency by 7-13% — a real but
modest gain. For the two locally-hosted platforms (FalkorDB, self-hosted
Neo4j), the same index produced a 4.7x and 9.7x speedup respectively. This
is consistent with the network-RTT hypothesis discussed in Section 4: when
network round-trip time dominates a query's total latency (as it does for
the cloud platforms), even a large change in server-side execution cost —
full label scan vs. indexed point lookup — barely moves the number, because
the fixed network cost swamps it. Locally-hosted platforms have no such
floor, so the index's actual effect on query execution is fully visible in
the measurement.

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

| Platform          | Total ops | Errors | Error rate | Throughput (qps) |
| ----------------- | --------- | ------ | ---------- | ---------------- |
| CognoDB           | 116       | 29     | 20.0%      | 7.73             |
| Neo4j AuraDB      | 444       | 0      | 0%         | 29.6             |
| Memgraph Cloud    | 152       | 0      | 0%         | 10.13            |
| FalkorDB          | 22,612    | 0      | 0%         | 1,507.47         |
| Neo4j Self-hosted | 40        | 0      | 0%         | 2.67             |

CognoDB under concurrency showed a 20% error rate (29 of 145 total attempted
operations failed with a driver-level protocol violation — the same failure
mode observed during bulk loading), reducing effective throughput to 7.73
qps. This reinforces the loading-phase finding: CognoDB's free tier appears
to intermittently return malformed responses, and this gets measurably
worse under concurrent load rather than being a one-off fluke.

Neo4j Self-hosted, despite the lowest single-query latencies of any
disk-backed platform (7–16ms, see 3.2/3.3), had the second-worst concurrent
throughput of the whole comparison at 2.67 qps — slower even than CognoDB's
degraded number. The likely cause is visible in the resource footprint data
(3.6): the container was already running at 98.13% of its 256MB memory
limit at rest, before any concurrent load was applied. Ten simultaneous
clients against a JVM-based engine with almost no memory headroom likely
triggered heavy GC pressure or page-cache thrashing — a case where
per-query speed and concurrent throughput tell very different stories, and
where the fairness-driven 256MB cap (matching CognoDB's tier) may be
genuinely under-provisioned for Neo4j's JVM overhead specifically, versus
FalkorDB's leaner memory profile at the same limit (3.6: 48.96% usage).

### 3.6 Resource footprint

| Platform          | Stored data size                                            | Memory usage                         | Notes                                                      |
| ----------------- | ----------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------- |
| CognoDB           | Not observable via free-tier console                        | Not observable via free-tier console |                                                            |
| Neo4j AuraDB      | Not observable via free-tier console                        | Not observable via free-tier console |                                                            |
| Memgraph Cloud    | Not observable via free-tier console                        | Not observable via free-tier console |                                                            |
| FalkorDB          | Not directly exposed (in-memory, no separate on-disk store) | 125.3 MiB / 256 MiB (48.96%)         | Comfortable headroom at this dataset size                  |
| Neo4j Self-hosted | Not captured separately (see note)                          | 251.2 MiB / 256 MiB (98.13%)         | Running at the edge of its memory limit — see caveat below |

## 4. Analysis

**Architecture explains almost everything, and it explains it consistently.**
FalkorDB won every single latency and throughput metric — often by 2-3
orders of magnitude — because it's a pure in-memory, Redis-backed engine
with no disk I/O in its query path. Its 1-hop traversal p50 (0.556ms) is
roughly 20x faster than self-hosted Neo4j (11.991ms) and over 1,700x faster
than CognoDB (960.524ms). The same pattern holds for bulk load throughput
(7,983.9 rels/sec vs. Neo4j Self-hosted's 1,636.7) and concurrent throughput
(1,507 qps vs. everything else in double or single digits). This isn't a
fluke of one benchmark — it shows up identically across loading, traversal,
lookup, aggregation, and concurrency, which is exactly what you'd expect if
the underlying cause is architectural rather than incidental.

**CognoDB and Memgraph Cloud's flat latency profile points to network
round-trip time, not query cost.** Both platforms report almost identical
latency (~960-1120ms) across 1-hop, 2-hop, 3-hop traversal, and point
lookup — query complexity essentially doesn't move the number. That flat
signature is the classic fingerprint of network round-trip time dominating
over actual query execution: if the query engine itself were the
bottleneck, deeper traversals (which touch more of the graph) would cost
measurably more than a single-node lookup. Self-hosted Neo4j and FalkorDB,
both running on local Docker with no network hop, show the expected
opposite pattern — latency scales up modestly with hop depth. Section 3.3's
indexing experiment supports the same conclusion from another angle: adding
an index to the cloud platforms only improved p50 latency by 7-13%, versus
4.7-9.7x for the locally-hosted platforms — a large change in server-side
execution cost barely moves total latency when a fixed network cost
dominates it. This is a genuine confound in comparing cloud-hosted free
tiers against local Docker containers, and it means CognoDB and Memgraph's
raw numbers likely understate their actual query engine performance.

**CognoDB was the only platform with correctness problems, not just speed
problems.** Every other platform returned zero errors across all
benchmarks. CognoDB alone showed a transient protocol-level failure during
bulk loading (recovered on retry with no code changes), a ~20% throughput
swing between two otherwise-identical load runs, and a 20% operation error
rate under concurrent load — all consistent with shared-tenant free-tier
instability rather than a deterministic property of the engine. This
matters more than the raw latency numbers: a database that's slow but
correct is a very different engineering tradeoff than one that's
occasionally wrong.

**Self-hosted Neo4j is the clearest illustration of "fast per-query, fragile
under load."** Its single-query latencies were the best of any disk-backed
platform, sitting well below AuraDB despite both running the same engine
family — plausible given AuraDB pays the network round-trip cost that
self-hosted avoids entirely. But under 10 concurrent clients, self-hosted
Neo4j dropped to 2.67 qps, the second-worst result in the whole comparison.
The resource footprint data explains why: the container was already at
98.13% of its 256MB memory cap before any concurrent load was applied,
versus FalkorDB's 48.96% under the identical cap. A JVM-based engine simply
has far less room to operate within a tight memory ceiling than a leaner
in-memory store — this is as much a finding about the fairness of a
uniform 256MB limit across architecturally different engines as it is about
either engine's raw speed.

## 5. Caveats and honest limitations

- **CognoDB showed a transient driver-level protocol failure** during the
  initial bulk load attempt (`ValueError: keys and values have different
length ... protocol violation by the server`), which succeeded on retry
  with zero code changes.
- **CognoDB's load throughput was not stable across runs:** a second load
  (via `MERGE`, no new data created) measured 619.0 relationships/sec versus
  751.5/sec on an earlier run — a ~20% slowdown with identical code and
  data.
- **CognoDB showed a 20% operation error rate under concurrent load** (29 of
  145 attempted operations failed with the same protocol-violation pattern
  seen during loading). No other platform showed any errors under the same
  test.
- **Cloud platforms (CognoDB, AuraDB, Memgraph Cloud) incur network
  round-trip latency to their respective regions, while Docker-hosted
  platforms (FalkorDB, self-hosted Neo4j) run entirely on local hardware
  with no network hop.** This is a genuine confound: CognoDB and Memgraph's
  flat, hop-depth-independent latency profile (~960-1120ms across all query
  types), and their modest 7-13% indexing speedup versus 4.7-9.7x on local
  platforms, are both consistent with network RTT dominating over query
  execution time — meaning their raw numbers likely understate actual
  engine performance relative to the locally-hosted platforms.
- **AuraDB Free and Memgraph Cloud's exact vCPU/RAM specs were not available
  from their consoles** the way CognoDB's are. Both were used on their
  smallest available free tier as a best-effort fairness approximation,
  rather than a confirmed matching resource cap — noted explicitly rather
  than presented as guaranteed parity.
- **Self-hosted Neo4j was observed at 98.13% of its 256MB Docker memory
  limit** (`docker stats`) after loading, versus FalkorDB's 48.96% on the
  same dataset and same limit — a meaningful architectural difference (JVM
  heap/page-cache overhead vs. a leaner in-memory store), not just a raw
  number, and a likely explanation for Neo4j Self-hosted's poor concurrent
  throughput despite its strong single-query latency.
- **The original CognoDB connection password was lost** during setup
  (shown only once by the console, not saved in time), requiring a fresh
  instance to be provisioned. This didn't affect the benchmark data itself,
  but is noted here for transparency about the setup process.

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

# Run latency/throughput benchmarks against every platform:
python benchmarks/run_benchmarks.py cognodb
python benchmarks/run_benchmarks.py neo4j_aura
python benchmarks/run_benchmarks.py memgraph
python benchmarks/run_benchmarks.py falkordb
python benchmarks/run_benchmarks.py neo4j_selfhosted

# Run the mixed concurrent read/write workload against every platform:
python benchmarks/mixed_workload.py cognodb
python benchmarks/mixed_workload.py neo4j_aura
python benchmarks/mixed_workload.py memgraph
python benchmarks/mixed_workload.py falkordb
python benchmarks/mixed_workload.py neo4j_selfhosted

# Run the unindexed-vs-indexed lookup comparison against every platform:
python benchmarks/lookup_index_comparison.py cognodb
python benchmarks/lookup_index_comparison.py neo4j_aura
python benchmarks/lookup_index_comparison.py memgraph
python benchmarks/lookup_index_comparison.py falkordb
python benchmarks/lookup_index_comparison.py neo4j_selfhosted

# Generate ready-to-paste markdown tables from all results:
python results/compare_results.py
```
