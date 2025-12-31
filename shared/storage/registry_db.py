"""RegistryDB - SQLite-backed artifact registry.

Tracks all artifacts across tools for:
- Cross-tool artifact discovery
- Lineage tracking
- Garbage collection

Per ADR-0009: All timestamps are ISO-8601 UTC.
"""

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from shared.contracts.core.artifact_registry import (
    ArtifactQuery,
    ArtifactRecord,
    ArtifactState,
    ArtifactStats,
    ArtifactType,
)
from shared.storage.artifact_store import get_workspace_path

__version__ = "0.1.0"

SCHEMA_VERSION = 1

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    artifact_type TEXT NOT NULL,
    name TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    locked_at TEXT,
    unlocked_at TEXT,
    state TEXT NOT NULL DEFAULT 'active',
    created_by_tool TEXT NOT NULL,
    parent_ids TEXT NOT NULL DEFAULT '[]',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    row_count INTEGER,
    column_count INTEGER,
    tags TEXT NOT NULL DEFAULT '[]',
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_tool ON artifacts(created_by_tool);
CREATE INDEX IF NOT EXISTS idx_artifacts_state ON artifacts(state);
CREATE INDEX IF NOT EXISTS idx_artifacts_created_at ON artifacts(created_at);

-- Reverse index for efficient lineage children lookup (per ADR-0026)
CREATE TABLE IF NOT EXISTS lineage_edges (
    parent_id TEXT NOT NULL,
    child_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (parent_id, child_id)
);

CREATE INDEX IF NOT EXISTS idx_lineage_parent ON lineage_edges(parent_id);
CREATE INDEX IF NOT EXISTS idx_lineage_child ON lineage_edges(child_id);
"""


class RegistryDB:
    """SQLite-backed artifact registry."""

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            workspace = get_workspace_path()
            workspace.mkdir(parents=True, exist_ok=True)
            db_path = workspace / ".registry.db"
        self.db_path = db_path

    async def initialize(self) -> None:
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(CREATE_TABLES_SQL)

            # Check/set schema version
            cursor = await db.execute(
                "SELECT version FROM schema_version LIMIT 1"
            )
            row = await cursor.fetchone()
            if row is None:
                await db.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (SCHEMA_VERSION,)
                )
            await db.commit()

    @asynccontextmanager
    async def _connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get a database connection."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    async def register(self, record: ArtifactRecord) -> None:
        """Register an artifact in the registry."""
        async with self._connection() as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO artifacts (
                    artifact_id, artifact_type, name, relative_path,
                    created_at, updated_at, locked_at, unlocked_at,
                    state, created_by_tool, parent_ids, size_bytes,
                    row_count, column_count, tags, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.artifact_id,
                    record.artifact_type.value,
                    record.name,
                    record.relative_path,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                    record.locked_at.isoformat() if record.locked_at else None,
                    record.unlocked_at.isoformat() if record.unlocked_at else None,
                    record.state.value,
                    record.created_by_tool,
                    json.dumps(record.parent_ids),
                    record.size_bytes,
                    record.row_count,
                    record.column_count,
                    json.dumps(record.tags),
                    record.description,
                )
            )
            await db.commit()

    async def get(self, artifact_id: str) -> ArtifactRecord | None:
        """Get an artifact by ID."""
        async with self._connection() as db:
            cursor = await db.execute(
                "SELECT * FROM artifacts WHERE artifact_id = ?",
                (artifact_id,)
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return self._row_to_record(row)

    async def query(self, query: ArtifactQuery) -> list[ArtifactRecord]:
        """Query artifacts with filters."""
        conditions = []
        params = []

        if query.artifact_type:
            conditions.append("artifact_type = ?")
            params.append(query.artifact_type.value)

        if query.created_by_tool:
            conditions.append("created_by_tool = ?")
            params.append(query.created_by_tool)

        if query.state:
            conditions.append("state = ?")
            params.append(query.state.value)

        if query.parent_id:
            conditions.append("parent_ids LIKE ?")
            params.append(f'%"{query.parent_id}"%')

        if query.created_after:
            conditions.append("created_at >= ?")
            params.append(query.created_after.isoformat())

        if query.created_before:
            conditions.append("created_at <= ?")
            params.append(query.created_before.isoformat())

        if query.name_contains:
            conditions.append("name LIKE ?")
            params.append(f"%{query.name_contains}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"""
            SELECT * FROM artifacts
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([query.limit, query.offset])

        async with self._connection() as db:
            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()
            return [self._row_to_record(row) for row in rows]

    async def get_stats(self) -> ArtifactStats:
        """Get summary statistics for the registry."""
        async with self._connection() as db:
            # Total count and size
            cursor = await db.execute(
                "SELECT COUNT(*), SUM(size_bytes) FROM artifacts"
            )
            row = await cursor.fetchone()
            total_count = row[0] or 0
            total_size = row[1] or 0

            # By type
            cursor = await db.execute(
                "SELECT artifact_type, COUNT(*) FROM artifacts GROUP BY artifact_type"
            )
            by_type = {row[0]: row[1] for row in await cursor.fetchall()}

            # By tool
            cursor = await db.execute(
                "SELECT created_by_tool, COUNT(*) FROM artifacts GROUP BY created_by_tool"
            )
            by_tool = {row[0]: row[1] for row in await cursor.fetchall()}

            # By state
            cursor = await db.execute(
                "SELECT state, COUNT(*) FROM artifacts GROUP BY state"
            )
            by_state = {row[0]: row[1] for row in await cursor.fetchall()}

        return ArtifactStats(
            total_artifacts=total_count,
            total_size_bytes=total_size,
            by_type=by_type,
            by_tool=by_tool,
            by_state=by_state,
        )

    async def update_state(
        self,
        artifact_id: str,
        state: ArtifactState,
    ) -> None:
        """Update artifact state (per ADR-0002: preserve on unlock)."""
        now = datetime.now(UTC).isoformat()

        async with self._connection() as db:
            if state == ArtifactState.LOCKED:
                await db.execute(
                    "UPDATE artifacts SET state = ?, locked_at = ?, updated_at = ? WHERE artifact_id = ?",
                    (state.value, now, now, artifact_id)
                )
            elif state == ArtifactState.UNLOCKED:
                await db.execute(
                    "UPDATE artifacts SET state = ?, unlocked_at = ?, updated_at = ? WHERE artifact_id = ?",
                    (state.value, now, now, artifact_id)
                )
            else:
                await db.execute(
                    "UPDATE artifacts SET state = ?, updated_at = ? WHERE artifact_id = ?",
                    (state.value, now, artifact_id)
                )
            await db.commit()

    async def get_children(self, parent_id: str) -> list[str]:
        """Get child artifact IDs efficiently using reverse index (per ADR-0026).
        
        This uses O(1) index lookup instead of O(n) full scan.
        """
        async with self._connection() as db:
            cursor = await db.execute(
                "SELECT child_id FROM lineage_edges WHERE parent_id = ?",
                (parent_id,)
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def get_parents(self, child_id: str) -> list[str]:
        """Get parent artifact IDs efficiently using reverse index."""
        async with self._connection() as db:
            cursor = await db.execute(
                "SELECT parent_id FROM lineage_edges WHERE child_id = ?",
                (child_id,)
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def _update_lineage_edges(
        self,
        artifact_id: str,
        parent_ids: list[str],
    ) -> None:
        """Update lineage edges for an artifact."""
        now = datetime.now(UTC).isoformat()
        async with self._connection() as db:
            # Remove old edges
            await db.execute(
                "DELETE FROM lineage_edges WHERE child_id = ?",
                (artifact_id,)
            )
            # Add new edges
            for parent_id in parent_ids:
                await db.execute(
                    "INSERT OR IGNORE INTO lineage_edges (parent_id, child_id, created_at) VALUES (?, ?, ?)",
                    (parent_id, artifact_id, now)
                )
            await db.commit()

    def _row_to_record(self, row: aiosqlite.Row) -> ArtifactRecord:
        """Convert a database row to an ArtifactRecord."""
        return ArtifactRecord(
            artifact_id=row["artifact_id"],
            artifact_type=ArtifactType(row["artifact_type"]),
            name=row["name"],
            relative_path=row["relative_path"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            locked_at=datetime.fromisoformat(row["locked_at"]) if row["locked_at"] else None,
            unlocked_at=datetime.fromisoformat(row["unlocked_at"]) if row["unlocked_at"] else None,
            state=ArtifactState(row["state"]),
            created_by_tool=row["created_by_tool"],
            parent_ids=json.loads(row["parent_ids"]),
            size_bytes=row["size_bytes"],
            row_count=row["row_count"],
            column_count=row["column_count"],
            tags=json.loads(row["tags"]),
            description=row["description"],
        )
