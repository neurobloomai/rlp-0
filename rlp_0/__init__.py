"""
RLP-0: Relational Ledger Protocol - Zero

A minimal state primitive for relational infrastructure.
"""

from .semantic import RelationalState
from .signals import Signal, RUPTURE_DETECTED
from .gates import Gate
from .core import RLP0

__version__ = "0.1.0"
__all__ = ["RLP0", "RelationalState", "Signal", "RUPTURE_DETECTED", "Gate"]
