"""
RLP-0 Storage Layer

SQLite-backed persistence for RelationalState. Implements the storage
layer described in the three-layer architecture: semantic → protocol → storage.

The semantic layer is independent of this module. Any other backend (graph DB,
distributed ledger, file system) can replace it without changing RLP-0's meaning.

Tables
------
relationships
    One row per (from_id, to_id) pair — current relational state.
    Upserted on every update_state() call.

state_history
    Append-only log of every state change — basis for drift detection,
    audit trails, and future trust inference.
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from .semantic import RelationalState

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS relationships (
    from_id         TEXT NOT NULL,
    to_id           TEXT NOT NULL,
    trust           REAL NOT NULL DEFAULT 1.0,
    intent          REAL NOT NULL DEFAULT 1.0,
    narrative       REAL NOT NULL DEFAULT 1.0,
    commitments     REAL NOT NULL DEFAULT 1.0,
    rupture_risk    REAL NOT NULL DEFAULT 0.0,
    is_gated        INTEGER NOT NULL DEFAULT 0,
    last_updated    TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id)
);

CREATE TABLE IF NOT EXISTS state_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id         TEXT NOT NULL,
    to_id           TEXT NOT NULL,
    recorded_at     TEXT NOT NULL,
    trust           REAL NOT NULL,
    intent          REAL NOT NULL,
    narrative       REAL NOT NULL,
    commitments     REAL NOT NULL,
    rupture_risk    REAL NOT NULL,
    is_gated        INTEGER NOT NULL,
    change_type     TEXT NOT NULL DEFAULT 'update',
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_history_pair
    ON state_history (from_id, to_id, recorded_at);
"""


class RelationalStorage:
    """
    SQLite backend for RelationalState.

    Usage
    -----
    storage = RelationalStorage("rlp.db")
    storage.save("agent-a", "agent-b", state)

    state = storage.load("agent-a", "agent-b")   # None if not found
    history = storage.history("agent-a", "agent-b", limit=20)
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._path = str(db_path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        logger.debug("RelationalStorage opened at %s", self._path)

    # ── Write ─────────────────────────────────────────────────────────────────

    def save(
        self,
        from_id: str,
        to_id: str,
        state: RelationalState,
        change_type: str = "update",
        notes: Optional[str] = None,
    ) -> None:
        """Upsert current state and append to history log."""
        now = datetime.now(timezone.utc).isoformat()

        self._conn.execute(
            """
            INSERT INTO relationships
                (from_id, to_id, trust, intent, narrative, commitments,
                 rupture_risk, is_gated, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (from_id, to_id) DO UPDATE SET
                trust        = excluded.trust,
                intent       = excluded.intent,
                narrative    = excluded.narrative,
                commitments  = excluded.commitments,
                rupture_risk = excluded.rupture_risk,
                is_gated     = excluded.is_gated,
                last_updated = excluded.last_updated
            """,
            (
                from_id, to_id,
                state.trust, state.intent, state.narrative, state.commitments,
                state.rupture_risk, int(state.is_gated), now,
            ),
        )

        self._conn.execute(
            """
            INSERT INTO state_history
                (from_id, to_id, recorded_at, trust, intent, narrative,
                 commitments, rupture_risk, is_gated, change_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                from_id, to_id, now,
                state.trust, state.intent, state.narrative, state.commitments,
                state.rupture_risk, int(state.is_gated),
                change_type, notes,
            ),
        )

        self._conn.commit()

    # ── Read ──────────────────────────────────────────────────────────────────

    def load(self, from_id: str, to_id: str) -> Optional[RelationalState]:
        """Load most recent state for a pair. Returns None if not found."""
        row = self._conn.execute(
            "SELECT * FROM relationships WHERE from_id = ? AND to_id = ?",
            (from_id, to_id),
        ).fetchone()

        if row is None:
            return None

        return RelationalState(
            trust       = row["trust"],
            intent      = row["intent"],
            narrative   = row["narrative"],
            commitments = row["commitments"],
            rupture_risk = row["rupture_risk"],
            is_gated    = bool(row["is_gated"]),
            last_updated = datetime.fromisoformat(row["last_updated"]),
        )

    def history(
        self,
        from_id: str,
        to_id: str,
        limit: int = 50,
    ) -> List[dict]:
        """Return state change history for a pair, newest first."""
        rows = self._conn.execute(
            """
            SELECT recorded_at, trust, intent, narrative, commitments,
                   rupture_risk, is_gated, change_type, notes
            FROM state_history
            WHERE from_id = ? AND to_id = ?
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (from_id, to_id, limit),
        ).fetchall()

        return [dict(r) for r in rows]

    def all_pairs(self) -> List[Tuple[str, str]]:
        """Return all tracked (from_id, to_id) pairs."""
        rows = self._conn.execute(
            "SELECT from_id, to_id FROM relationships"
        ).fetchall()
        return [(r["from_id"], r["to_id"]) for r in rows]

    def gated_pairs(self) -> List[Tuple[str, str]]:
        """Return pairs where is_gated = 1."""
        rows = self._conn.execute(
            "SELECT from_id, to_id FROM relationships WHERE is_gated = 1"
        ).fetchall()
        return [(r["from_id"], r["to_id"]) for r in rows]

    def at_risk_pairs(self, threshold: float = 0.5) -> List[Tuple[str, str]]:
        """Return pairs with rupture_risk >= threshold."""
        rows = self._conn.execute(
            "SELECT from_id, to_id FROM relationships WHERE rupture_risk >= ?",
            (threshold,),
        ).fetchall()
        return [(r["from_id"], r["to_id"]) for r in rows]

    def delete(self, from_id: str, to_id: str) -> bool:
        """Remove a relationship and its history. Returns True if found."""
        cursor = self._conn.execute(
            "DELETE FROM relationships WHERE from_id = ? AND to_id = ?",
            (from_id, to_id),
        )
        self._conn.execute(
            "DELETE FROM state_history WHERE from_id = ? AND to_id = ?",
            (from_id, to_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        self._conn.close()
