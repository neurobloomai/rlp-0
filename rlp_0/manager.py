"""
RLP-0 Manager

Manages relational state across multiple agent pairs. A single RLP0
instance tracks one relationship; RLP0Manager tracks all of them.

This is the operational layer above the MVK — the thing a real system
binds to rather than juggling individual RLP0 instances.

Usage
-----
    from rlp_0 import RLP0Manager

    mgr = RLP0Manager(agent_id="agent-a", db_path="rlp.db")

    # Update primitives after an exchange
    mgr.update("agent-b", trust=0.9, intent=0.85)

    # Check before acting
    if not mgr.can_interact("agent-b"):
        print("blocked — repair required")

    # Scan health of all relationships
    for pair in mgr.at_risk():
        print(f"At risk: {pair}")
"""

import logging
from typing import Callable, Dict, List, Optional, Tuple

from .core import RLP0
from .semantic import RelationalState
from .signals import Signal
from .storage import RelationalStorage

logger = logging.getLogger(__name__)


class RLP0Manager:
    """
    Manages RLP-0 state across multiple (self ↔ other) relationships.

    Parameters
    ----------
    agent_id : str
        Identity of the agent this manager belongs to.
    rupture_threshold : float
        Threshold applied to all managed relationships (default 0.6).
    db_path : str
        SQLite path for persistence. ":memory:" (default) is in-memory only.
    on_rupture : callable, optional
        Called with (other_agent_id, Signal) whenever RUPTURE_DETECTED fires.
    on_repair : callable, optional
        Called with (other_agent_id, Signal) whenever REPAIR_COMPLETE fires.
    """

    def __init__(
        self,
        agent_id: str,
        rupture_threshold: float = 0.6,
        db_path: str = ":memory:",
        on_rupture: Optional[Callable[[str, Signal], None]] = None,
        on_repair:  Optional[Callable[[str, Signal], None]] = None,
    ) -> None:
        self.agent_id         = agent_id
        self._threshold       = rupture_threshold
        self._storage         = RelationalStorage(db_path)
        self._on_rupture      = on_rupture
        self._on_repair       = on_repair
        self._pairs: Dict[str, RLP0] = {}

        # Restore from storage
        for from_id, to_id in self._storage.all_pairs():
            if from_id == self.agent_id:
                state = self._storage.load(from_id, to_id)
                if state:
                    self._pairs[to_id] = self._make_rlp(to_id, state)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _make_rlp(self, other_id: str, state: Optional[RelationalState] = None) -> RLP0:
        rlp = RLP0(
            rupture_threshold=self._threshold,
            state=state,
        )

        def _on_signal(signal: Signal) -> None:
            from .signals import RUPTURE_DETECTED, REPAIR_COMPLETE
            if signal.signal_type == RUPTURE_DETECTED and self._on_rupture:
                self._on_rupture(other_id, signal)
            elif signal.signal_type == REPAIR_COMPLETE and self._on_repair:
                self._on_repair(other_id, signal)
            # Persist after every signal (state changed)
            self._storage.save(
                self.agent_id, other_id, rlp.state,
                change_type=signal.signal_type.name.lower(),
            )

        rlp.subscribe(_on_signal)
        return rlp

    def _get_or_create(self, other_id: str) -> RLP0:
        if other_id not in self._pairs:
            self._pairs[other_id] = self._make_rlp(other_id)
            self._storage.save(
                self.agent_id, other_id,
                self._pairs[other_id].state,
                change_type="created",
            )
        return self._pairs[other_id]

    # ── Public API ────────────────────────────────────────────────────────────

    def update(
        self,
        other_id: str,
        trust:       Optional[float] = None,
        intent:      Optional[float] = None,
        narrative:   Optional[float] = None,
        commitments: Optional[float] = None,
    ) -> RLP0:
        """
        Update relational primitives for a specific relationship.
        Persists the new state and fires signals if rupture threshold is crossed.

        Returns the RLP0 instance for the pair.
        """
        rlp = self._get_or_create(other_id)
        rlp.update_state(
            trust=trust,
            intent=intent,
            narrative=narrative,
            commitments=commitments,
        )
        self._storage.save(self.agent_id, other_id, rlp.state)
        return rlp

    def acknowledge_repair(self, other_id: str) -> bool:
        """
        Acknowledge repair for a specific relationship.
        Only releases the gate if primitives have actually recovered.

        Returns True if gate was released, False if insufficient repair.
        """
        rlp = self._get_or_create(other_id)
        released = rlp.acknowledge_repair()
        if released:
            self._storage.save(
                self.agent_id, other_id, rlp.state,
                change_type="repair_complete",
            )
        return released

    def can_interact(self, other_id: str) -> bool:
        """Return True if the relationship gate is open (not gated)."""
        return self._get_or_create(other_id).check_gate()

    def state(self, other_id: str) -> RelationalState:
        """Return current relational state for a pair."""
        return self._get_or_create(other_id).state

    def rupture_risk(self, other_id: str) -> float:
        """Return current rupture risk for a pair."""
        return self._get_or_create(other_id).rupture_risk

    def is_gated(self, other_id: str) -> bool:
        """Return True if the pair is currently gated."""
        return self._get_or_create(other_id).is_gated

    def history(self, other_id: str, limit: int = 50) -> list:
        """Return state change history for a relationship."""
        return self._storage.history(self.agent_id, other_id, limit=limit)

    # ── Fleet view ────────────────────────────────────────────────────────────

    def gated(self) -> List[str]:
        """Return IDs of all currently gated relationships."""
        return [aid for aid, rlp in self._pairs.items() if rlp.is_gated]

    def at_risk(self, threshold: Optional[float] = None) -> List[str]:
        """Return IDs of relationships at or above the rupture risk threshold."""
        t = threshold if threshold is not None else self._threshold
        return [aid for aid, rlp in self._pairs.items() if rlp.rupture_risk >= t]

    def healthy(self) -> List[str]:
        """Return IDs of relationships that are open and below risk threshold."""
        return [
            aid for aid, rlp in self._pairs.items()
            if not rlp.is_gated and rlp.rupture_risk < self._threshold
        ]

    def all_pairs(self) -> List[str]:
        """Return IDs of all tracked relationships."""
        return list(self._pairs.keys())

    def summary(self) -> dict:
        """Return an observability snapshot across all relationships."""
        return {
            "agent_id":       self.agent_id,
            "relationships":  len(self._pairs),
            "healthy":        len(self.healthy()),
            "at_risk":        len(self.at_risk()),
            "gated":          len(self.gated()),
            "threshold":      self._threshold,
        }

    def close(self) -> None:
        """Close the storage connection."""
        self._storage.close()
