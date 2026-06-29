"""
RLP-0: Relational Ledger Protocol - Zero

A minimal state primitive for relational infrastructure.
"""

from .semantic import RelationalState
from .signals import Signal, RUPTURE_DETECTED, REPAIR_COMPLETE
from .gates import Gate
from .core import RLP0
from .storage import RelationalStorage
from .manager import RLP0Manager

__version__ = "0.2.0"
__all__ = [
    "RLP0",
    "RLP0Manager",
    "RelationalState",
    "RelationalStorage",
    "Signal",
    "RUPTURE_DETECTED",
    "REPAIR_COMPLETE",
    "Gate",
]
