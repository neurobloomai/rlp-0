"""
Signals - RLP-0 upward communication

RLP-0 is semantically active but operationally minimal.
It can emit signals but cannot perform actions.

Signals nudge upward; they don't speak upward.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional, Callable, List


class SignalType(Enum):
    """Types of signals RLP-0 can emit."""
    RUPTURE_DETECTED = auto()


@dataclass
class Signal:
    """
    A signal emitted by RLP-0.
    
    Signals are observations, not commands.
    Expression protocols decide how to respond.
    """
    signal_type: SignalType
    timestamp: datetime
    rupture_risk: float
    context: Optional[str] = None
    
    def __str__(self) -> str:
        return f"[{self.signal_type.name}] risk={self.rupture_risk:.2f} at {self.timestamp.isoformat()}"


# Convenience constant
RUPTURE_DETECTED = SignalType.RUPTURE_DETECTED


class SignalBus:
    """
    Simple signal bus for RLP-0 to emit signals.
    Expression protocols subscribe to receive signals.
    """
    
    def __init__(self):
        self._subscribers: List[Callable[[Signal], None]] = []
        self._history: List[Signal] = []
    
    def subscribe(self, callback: Callable[[Signal], None]) -> None:
        """Subscribe to receive signals."""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[Signal], None]) -> None:
        """Unsubscribe from signals."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def emit(self, signal: Signal) -> None:
        """Emit a signal to all subscribers."""
        self._history.append(signal)
        for subscriber in self._subscribers:
            subscriber(signal)
    
    @property
    def history(self) -> List[Signal]:
        """Return signal history."""
        return self._history.copy()
