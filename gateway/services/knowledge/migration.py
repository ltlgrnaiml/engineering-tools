"""Database Migration - SPEC-0043-AR05.

Migrate legacy llm_logs.db to knowledge.db.
"""

import sqlite3
from pathlib import Path


def migrate_llm_logs(source_db: Path, target_conn: sqlite3.Connection) -> int:
    """Migrate LLM call logs from legacy database.

    Args:
        source_db: Path to legacy llm_logs.db
        target_conn: Connection to knowledge.db

    Returns:
        Number of records migrated
    """
    if not source_db.exists():
        return 0

    source = sqlite3.connect(source_db)
    source.row_factory = sqlite3.Row

    try:
        rows = source.execute("SELECT * FROM llm_calls").fetchall()
    except sqlite3.OperationalError:
        source.close()
        return 0

    migrated = 0
    for row in rows:
        try:
            target_conn.execute("""
                INSERT OR IGNORE INTO llm_calls
                (session_id, timestamp, model, prompt, response, tokens_in, tokens_out, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['session_id'] if 'session_id' in row.keys() else None,
                row['timestamp'] if 'timestamp' in row.keys() else None,
                row['model'] if 'model' in row.keys() else 'unknown',
                row.get('prompt'),
                row.get('response'),
                row.get('tokens_in', 0),
                row.get('tokens_out', 0),
                row.get('cost', 0.0)
            ))
            migrated += 1
        except Exception:
            continue

    target_conn.commit()
    source.close()
    return migrated
