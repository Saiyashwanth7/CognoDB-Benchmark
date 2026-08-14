"""
Unified client wrapper.

Why this exists: CognoDB, Neo4j AuraDB, Memgraph, and self-hosted Neo4j all
speak the SAME protocol (Bolt) and SAME query language (Cypher) — so one
BoltClient class handles all four. Only ArangoDB is different (its own
protocol + AQL query language), so it gets its own class.

This is the single biggest time-saver in this whole project: by choosing
4 Cypher-compatible platforms + 1 different one, you write ONE set of
Cypher queries and reuse them almost unchanged across most platforms,
instead of writing 5 totally separate query implementations.
"""

from neo4j import GraphDatabase
from falkordb import FalkorDB


class BoltClient:
    """Wraps CognoDB / Neo4j AuraDB / Memgraph / self-hosted Neo4j — all Cypher."""

    def __init__(self, uri, user, password):
        auth = (user, password) if user else None
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def run_write(self, cypher, **params):
        with self.driver.session() as session:
            return session.execute_write(lambda tx: list(tx.run(cypher, **params)))

    def run_auto(self, cypher, **params):
        """
        Runs a query as a standalone auto-committing statement, NOT wrapped in
        an explicit transaction. Needed for schema changes (like CREATE INDEX)
        on platforms like Memgraph, which reject index creation inside
        execute_write's managed transaction ("multicommand transaction").
        """
        with self.driver.session() as session:
            return list(session.run(cypher, **params))

    def run_read(self, cypher, **params):
        with self.driver.session() as session:
            return session.execute_read(lambda tx: list(tx.run(cypher, **params)))

    def close(self):
        self.driver.close()


class FalkorClient:
    """
    Wraps FalkorDB — a graph database built on Redis. Uses the Redis protocol,
    NOT Bolt, but its query language (Cypher-like, "GRAPH.QUERY" under the
    hood) is close enough to Cypher that most of your query strings can be
    reused almost unchanged. Genuinely different architecture though: it's
    in-memory and Redis-backed, which makes it an interesting point of
    contrast against disk-backed platforms like Neo4j/CognoDB in your
    analysis section (e.g. "why was FalkorDB faster/slower at X").
    """

    def __init__(self, host, port, password=None):
        self.db = FalkorDB(host=host, port=port, password=password)
        self.graph = self.db.select_graph("benchmark")

    def _to_dicts(self, result):
        header = [
            col[1] if isinstance(col, (list, tuple)) else col for col in result.header
        ]
        return [dict(zip(header, row)) for row in result.result_set]

    def run_write(self, cypher, **params):
        result = self.graph.query(cypher, params=params)
        return self._to_dicts(result)

    def run_read(self, cypher, **params):
        result = self.graph.query(cypher, params=params)
        return self._to_dicts(result)

    def close(self):
        pass


def get_client(platform_config):
    """Factory: returns the right client class based on driver_type in config."""
    if platform_config["driver_type"] == "bolt":
        return BoltClient(
            platform_config["uri"],
            platform_config["user"],
            platform_config["password"],
        )
    elif platform_config["driver_type"] == "falkordb":
        return FalkorClient(
            platform_config["host"],
            platform_config["port"],
            platform_config["password"],
        )
    raise ValueError(f"Unknown driver_type: {platform_config['driver_type']}")
