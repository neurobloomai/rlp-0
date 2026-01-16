"""
Semantic Layer - Core of RLP-0

Defines what a relationship means through four primitives:
- trust: confidence signal
- intent: directional signal
- narrative: coherence signal
- commitments: accountability signal
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class RelationalState:
    """
    The four primitives that constitute relational state.
    
    Each primitive is a float [0.0, 1.0] representing current level.
    """
    
    # The four primitives
    trust: float = 1.0           # confidence signal
    intent: float = 1.0          # directional signal  
    narrative: float = 1.0       # coherence signal
    commitments: float = 1.0     # accountability signal
    
    # Computed state
    rupture_risk: float = 0.0
    
    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_gated: bool = False
    
    def __post_init__(self):
        """Validate primitives are in valid range."""
        for primitive in ['trust', 'intent', 'narrative', 'commitments']:
            value = getattr(self, primitive)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{primitive} must be between 0.0 and 1.0, got {value}")
    
    def update(self, **kwargs) -> 'RelationalState':
        """
        Update primitives and return new state.
        Immutable - returns new instance.
        """
        new_values = {
            'trust': kwargs.get('trust', self.trust),
            'intent': kwargs.get('intent', self.intent),
            'narrative': kwargs.get('narrative', self.narrative),
            'commitments': kwargs.get('commitments', self.commitments),
            'rupture_risk': self.rupture_risk,
            'is_gated': self.is_gated,
        }
        return RelationalState(**new_values)
    
    def as_dict(self) -> dict:
        """Return state as dictionary."""
        return {
            'trust': self.trust,
            'intent': self.intent,
            'narrative': self.narrative,
            'commitments': self.commitments,
            'rupture_risk': self.rupture_risk,
            'is_gated': self.is_gated,
            'last_updated': self.last_updated.isoformat(),
        }
