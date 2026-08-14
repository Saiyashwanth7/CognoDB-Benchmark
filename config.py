"""
Central config — loads every platform's connection details from .env.

Why this pattern: the assignment explicitly says never commit passwords/URIs
to the repo. Reading from environment variables (via .env, which is
gitignored) means the code itself contains zero secrets.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Each entry describes one platform: its connection info + which "driver type"
# to use when connecting (this determines which client class handles it).
PLATFORMS = {
    "cognodb": {
        "driver_type": "bolt",  # CognoDB speaks Bolt/Cypher — same protocol as Neo4j
        "uri": os.getenv("COGNODB_URI"),
        "user": os.getenv("COGNODB_USER"),
        "password": os.getenv("COGNODB_PASSWORD"),
    },
    "neo4j_aura": {
        "driver_type": "bolt",
        "uri": os.getenv("NEO4J_URI"),
        "user": os.getenv("NEO4J_USER"),
        "password": os.getenv("NEO4J_PASSWORD"),
    },
    "memgraph": {
        "driver_type": "bolt",  # Memgraph is also Bolt/Cypher-compatible — hosted on Memgraph Cloud free tier
        "uri": os.getenv("MEMGRAPH_URI"),
        "user": os.getenv("MEMGRAPH_USER") or None,
        "password": os.getenv("MEMGRAPH_PASSWORD") or None,
    },
    "neo4j_selfhosted": {
        "driver_type": "bolt",  # Self-hosted Neo4j Community via Docker — 5th platform,
        "uri": os.getenv("NEO4J_SELFHOSTED_URI"),  # reuses Cypher code directly, isolates
        "user": os.getenv("NEO4J_SELFHOSTED_USER"),  # "managed cloud overhead" vs "raw self-hosted"
        "password": os.getenv("NEO4J_SELFHOSTED_PASSWORD"),
    },
    "falkordb": {
        "driver_type": "falkordb",  # Redis-based graph DB — different protocol, genuinely different architecture
        "host": os.getenv("FALKORDB_HOST"),
        "port": int(os.getenv("FALKORDB_PORT", 6379)),
        "password": os.getenv("FALKORDB_PASSWORD") or None,
    },
}

# Fairness settings — document these numbers in the README exactly as used
RESOURCE_LIMITS = {
    "vcpu": 0.5,
    "ram_mb": 256,
    "disk_gb": 1,
}

BENCHMARK_CONFIG = {
    "warmup_iterations": 10,
    "measured_iterations": 100,   # assignment asks for >= 100 per read workload
    "batch_size": 1000,           # rows per bulk-insert batch when loading
}
