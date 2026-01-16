"""
Tests for RLP-0 Minimum Viable Kernel

Demonstrates the core rupture detection → gate → repair flow.
"""

import pytest
from rlp_0 import RLP0, RelationalState, Signal, RUPTURE_DETECTED


class TestRelationalState:
    """Test the semantic layer primitives."""
    
    def test_default_state_is_healthy(self):
        state = RelationalState()
        assert state.trust == 1.0
        assert state.intent == 1.0
        assert state.narrative == 1.0
        assert state.commitments == 1.0
        assert state.rupture_risk == 0.0
        assert state.is_gated == False
    
    def test_primitives_must_be_in_range(self):
        with pytest.raises(ValueError):
            RelationalState(trust=1.5)
        with pytest.raises(ValueError):
            RelationalState(intent=-0.1)
    
    def test_state_update_is_immutable(self):
        state1 = RelationalState(trust=0.8)
        state2 = state1.update(trust=0.5)
        
        assert state1.trust == 0.8  # Original unchanged
        assert state2.trust == 0.5  # New state has update


class TestRLP0Core:
    """Test the core RLP-0 operations."""
    
    def test_initial_state_is_healthy(self):
        rlp = RLP0()
        assert rlp.rupture_risk == 0.0
        assert rlp.is_gated == False
        assert rlp.check_gate() == True
    
    def test_low_primitives_increase_rupture_risk(self):
        rlp = RLP0()
        rlp.update_state(trust=0.2)
        
        # Risk should increase when trust drops
        assert rlp.rupture_risk > 0
    
    def test_rupture_detected_when_threshold_crossed(self):
        signals_received = []
        
        def signal_handler(signal: Signal):
            signals_received.append(signal)
        
        rlp = RLP0(rupture_threshold=0.5)
        rlp.subscribe(signal_handler)
        
        # Drop all primitives to trigger rupture
        rlp.update_state(trust=0.2, intent=0.2, narrative=0.2, commitments=0.2)
        
        # Should have received RUPTURE_DETECTED
        assert len(signals_received) == 1
        assert signals_received[0].signal_type == RUPTURE_DETECTED
    
    def test_gate_closes_on_rupture(self):
        rlp = RLP0(rupture_threshold=0.5)
        
        # Start open
        assert rlp.check_gate() == True
        
        # Trigger rupture
        rlp.update_state(trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        
        # Gate should be closed
        assert rlp.check_gate() == False
        assert rlp.is_gated == True
    
    def test_repair_releases_gate(self):
        rlp = RLP0(rupture_threshold=0.5)
        
        # Trigger rupture
        rlp.update_state(trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        assert rlp.is_gated == True
        
        # Simulate repair by restoring primitives
        rlp.update_state(trust=0.9, intent=0.9, narrative=0.9, commitments=0.9)
        
        # Acknowledge repair
        released = rlp.acknowledge_repair()
        
        assert released == True
        assert rlp.is_gated == False
        assert rlp.check_gate() == True
    
    def test_acknowledge_repair_returns_false_if_not_gated(self):
        rlp = RLP0()
        
        # Not gated
        assert rlp.is_gated == False
        
        # Acknowledge should return False
        result = rlp.acknowledge_repair()
        assert result == False


class TestRuptureFlow:
    """Test the complete rupture → gate → repair flow."""
    
    def test_complete_flow(self):
        """
        Demonstrates the MVK flow:
        1. Exchange happens
        2. RLP-0: compute_rupture_risk()
        3. RLP-0: emit(RUPTURE_DETECTED)
        4. RLP-0: gate()
        5. HX/AX: [blocked - must repair]
        6. HX/AX: performs repair (protocol-specific)
        7. HX/AX: calls acknowledge_repair()
        8. RLP-0: validates, updates state, release()
        9. Normal flow resumes
        """
        signals = []
        
        # Setup
        rlp = RLP0(rupture_threshold=0.5)
        rlp.subscribe(lambda s: signals.append(s))
        
        # 1. Exchange happens - trust is damaged
        # (Expression protocol would determine this)
        
        # 2-4. Update triggers risk computation, signal, gate
        rlp.update_state(trust=0.1, intent=0.1, narrative=0.2, commitments=0.2)
        
        # Verify rupture was detected and gated
        assert len(signals) == 1
        assert signals[0].signal_type == RUPTURE_DETECTED
        assert rlp.is_gated == True
        
        # 5. HX/AX is blocked
        assert rlp.check_gate() == False
        
        # 6. HX/AX performs repair (restores primitives)
        rlp.update_state(trust=0.8, intent=0.8, narrative=0.8, commitments=0.8)
        
        # 7-8. Acknowledge repair → validate → release
        rlp.acknowledge_repair()
        
        # 9. Normal flow resumes
        assert rlp.check_gate() == True
        assert rlp.is_gated == False
    
    def test_status_inspection(self):
        """Verify status provides full visibility."""
        rlp = RLP0(rupture_threshold=0.5)
        
        # Trigger and repair
        rlp.update_state(trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        rlp.update_state(trust=0.9, intent=0.9, narrative=0.9, commitments=0.9)
        rlp.acknowledge_repair()
        
        status = rlp.status()
        
        # Should have state, gate history, signal count
        assert 'state' in status
        assert 'is_gated' in status
        assert 'gate_history' in status
        assert 'signal_count' in status
        
        # Gate history should show close and release
        assert len(status['gate_history']) == 2
        assert status['gate_history'][0]['action'] == 'closed'
        assert status['gate_history'][1]['action'] == 'released'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
