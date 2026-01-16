"""
Gates - RLP-0 flow control

Gates block interaction until repair is acknowledged.
RLP-0 controls the gate; expression protocols perform the repair.

This preserves layering:
- RLP-0 detects and gates
- HX/AX repairs
- RLP-0 validates and releases
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum, auto


class GateState(Enum):
    """State of the gate."""
    OPEN = auto()
    CLOSED = auto()


@dataclass
class GateEvent:
    """Record of a gate state change."""
    action: str  # 'closed' or 'released'
    timestamp: datetime
    reason: Optional[str] = None
    rupture_risk_at_event: float = 0.0


@dataclass
class Gate:
    """
    Controls flow between exchanges.
    
    When closed, interaction is blocked until repair is acknowledged.
    RLP-0 doesn't know what repair looks like - that's protocol-specific.
    It only knows: repair was claimed → validate → release.
    """
    
    state: GateState = GateState.OPEN
    closed_at: Optional[datetime] = None
    reason: Optional[str] = None
    history: List[GateEvent] = field(default_factory=list)
    
    @property
    def is_open(self) -> bool:
        return self.state == GateState.OPEN
    
    @property
    def is_closed(self) -> bool:
        return self.state == GateState.CLOSED
    
    def close(self, reason: str, rupture_risk: float) -> None:
        """
        Close the gate. Blocks until repair.
        Called by RLP-0 when rupture detected.
        """
        if self.is_closed:
            return  # Already closed
            
        self.state = GateState.CLOSED
        self.closed_at = datetime.now(timezone.utc)
        self.reason = reason
        
        self.history.append(GateEvent(
            action='closed',
            timestamp=self.closed_at,
            reason=reason,
            rupture_risk_at_event=rupture_risk
        ))
    
    def release(self, rupture_risk: float) -> None:
        """
        Release the gate. Allows interaction to resume.
        Called by RLP-0 after repair is acknowledged.
        """
        if self.is_open:
            return  # Already open
            
        self.state = GateState.OPEN
        
        self.history.append(GateEvent(
            action='released',
            timestamp=datetime.now(timezone.utc),
            reason='repair_acknowledged',
            rupture_risk_at_event=rupture_risk
        ))
        
        self.closed_at = None
        self.reason = None
    
    def check(self) -> bool:
        """
        Check if interaction can proceed.
        Returns True if gate is open.
        """
        return self.is_open
