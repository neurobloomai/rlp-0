"""
RLP-0 Core - Minimum Viable Kernel

The MVK implements:
- State: rupture_risk (float)
- Signals: RUPTURE_DETECTED
- Gates: block_until_repair(), release()
- Operations: compute_rupture_risk(), acknowledge_repair()

RLP-0 is semantically active but operationally minimal.
Active signaling, not active acting.
"""

from datetime import datetime, timezone
from typing import Optional, Callable, List

from .semantic import RelationalState
from .signals import Signal, SignalType, SignalBus, RUPTURE_DETECTED
from .gates import Gate


class RLP0:
    """
    Relational Ledger Protocol - Zero
    
    A minimal state primitive for relational infrastructure.
    
    RLP-0 senses and signals, but does not decide how to respond.
    That is the expression layer's job.
    """
    
    # Default threshold for rupture detection
    DEFAULT_RUPTURE_THRESHOLD = 0.6
    
    def __init__(
        self,
        rupture_threshold: float = DEFAULT_RUPTURE_THRESHOLD,
        state: Optional[RelationalState] = None
    ):
        """
        Initialize RLP-0.
        
        Args:
            rupture_threshold: Risk level [0.0, 1.0] that triggers RUPTURE_DETECTED
            state: Initial relational state (defaults to healthy state)
        """
        self._state = state or RelationalState()
        self._gate = Gate()
        self._signal_bus = SignalBus()
        self._rupture_threshold = rupture_threshold
        
    # ─────────────────────────────────────────────────────────────
    # State Access
    # ─────────────────────────────────────────────────────────────
    
    @property
    def state(self) -> RelationalState:
        """Current relational state (read-only)."""
        return self._state
    
    @property
    def rupture_risk(self) -> float:
        """Current rupture risk level."""
        return self._state.rupture_risk
    
    @property
    def is_gated(self) -> bool:
        """Whether interaction is currently blocked."""
        return self._gate.is_closed
    
    # ─────────────────────────────────────────────────────────────
    # Signal Subscription
    # ─────────────────────────────────────────────────────────────
    
    def subscribe(self, callback: Callable[[Signal], None]) -> None:
        """Subscribe to RLP-0 signals."""
        self._signal_bus.subscribe(callback)
    
    def unsubscribe(self, callback: Callable[[Signal], None]) -> None:
        """Unsubscribe from signals."""
        self._signal_bus.unsubscribe(callback)
    
    @property
    def signal_history(self) -> List[Signal]:
        """History of emitted signals."""
        return self._signal_bus.history
    
    # ─────────────────────────────────────────────────────────────
    # Core Operations
    # ─────────────────────────────────────────────────────────────
    
    def update_state(
        self,
        trust: Optional[float] = None,
        intent: Optional[float] = None,
        narrative: Optional[float] = None,
        commitments: Optional[float] = None
    ) -> None:
        """
        Update relational state primitives.
        
        Called by expression protocols after exchanges.
        Automatically computes rupture risk and may emit signals.
        """
        # Build update kwargs
        updates = {}
        if trust is not None:
            updates['trust'] = trust
        if intent is not None:
            updates['intent'] = intent
        if narrative is not None:
            updates['narrative'] = narrative
        if commitments is not None:
            updates['commitments'] = commitments
        
        # Update state
        if updates:
            self._state = self._state.update(**updates)
        
        # Compute and respond to rupture risk
        self.compute_rupture_risk()
    
    def compute_rupture_risk(self) -> float:
        """
        Compute rupture risk from current state.
        
        MVK uses simple average of inverse primitives.
        Future versions may use more sophisticated computation.
        
        If risk exceeds threshold:
        1. Emits RUPTURE_DETECTED signal
        2. Closes gate until repair
        
        Returns:
            Current rupture risk [0.0, 1.0]
        """
        # Simple risk computation: average of (1 - primitive)
        # Low primitives = high risk
        risk = (
            (1 - self._state.trust) +
            (1 - self._state.intent) +
            (1 - self._state.narrative) +
            (1 - self._state.commitments)
        ) / 4
        
        # Update state with computed risk
        self._state.rupture_risk = risk
        self._state.last_updated = datetime.now(timezone.utc)
        
        # Check threshold
        if risk >= self._rupture_threshold and self._gate.is_open:
            self._emit_rupture_detected(risk)
            self._gate.close(
                reason=f"rupture_risk={risk:.2f} >= threshold={self._rupture_threshold}",
                rupture_risk=risk
            )
            self._state.is_gated = True
        
        return risk
    
    def acknowledge_repair(self) -> bool:
        """
        Acknowledge that repair has been performed.
        
        Called by expression protocols (HX/AX) after performing repair.
        RLP-0 validates repair occurred and releases the gate.
        
        MVK validation: trust + log (repair claimed → accepted)
        Future versions may recompute risk and require threshold.
        
        Returns:
            True if gate was released, False if wasn't gated
        """
        if not self.is_gated:
            return False
        
        # MVK: trust the expression protocol's repair claim
        # Log is implicit in gate history
        
        # Recompute risk (repair should have improved primitives)
        self.compute_rupture_risk()
        
        # Release gate
        self._gate.release(rupture_risk=self._state.rupture_risk)
        self._state.is_gated = False
        
        return True
    
    def check_gate(self) -> bool:
        """
        Check if interaction can proceed.
        
        Returns:
            True if gate is open (can proceed)
            False if gated (must repair)
        """
        return self._gate.check()
    
    # ─────────────────────────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────────────────────────
    
    def _emit_rupture_detected(self, risk: float) -> None:
        """Emit RUPTURE_DETECTED signal."""
        signal = Signal(
            signal_type=RUPTURE_DETECTED,
            timestamp=datetime.now(timezone.utc),
            rupture_risk=risk,
            context=f"Rupture risk {risk:.2f} exceeded threshold {self._rupture_threshold}"
        )
        self._signal_bus.emit(signal)
    
    # ─────────────────────────────────────────────────────────────
    # Inspection
    # ─────────────────────────────────────────────────────────────
    
    def status(self) -> dict:
        """Return current status for inspection."""
        return {
            'state': self._state.as_dict(),
            'is_gated': self.is_gated,
            'rupture_threshold': self._rupture_threshold,
            'signal_count': len(self._signal_bus.history),
            'gate_history': [
                {
                    'action': e.action,
                    'timestamp': e.timestamp.isoformat(),
                    'reason': e.reason,
                    'rupture_risk': e.rupture_risk_at_event
                }
                for e in self._gate.history
            ]
        }
