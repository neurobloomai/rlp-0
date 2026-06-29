"""
Tests for RLP0Manager — multi-relationship management.
"""
import pytest
from rlp_0 import RLP0Manager, Signal, RUPTURE_DETECTED, REPAIR_COMPLETE


@pytest.fixture
def mgr():
    return RLP0Manager(agent_id="agent-a", rupture_threshold=0.5, db_path=":memory:")


class TestBasicManagement:
    def test_can_interact_returns_true_by_default(self, mgr):
        assert mgr.can_interact("agent-b") is True

    def test_update_creates_relationship(self, mgr):
        mgr.update("agent-b", trust=0.9)
        assert "agent-b" in mgr.all_pairs()

    def test_update_returns_rlp_instance(self, mgr):
        from rlp_0 import RLP0
        rlp = mgr.update("agent-b", trust=0.8)
        assert isinstance(rlp, RLP0)

    def test_state_reflects_updates(self, mgr):
        mgr.update("agent-b", trust=0.6, intent=0.7, narrative=0.8, commitments=0.9)
        state = mgr.state("agent-b")
        assert state.trust       == pytest.approx(0.6)
        assert state.intent      == pytest.approx(0.7)
        assert state.narrative   == pytest.approx(0.8)
        assert state.commitments == pytest.approx(0.9)

    def test_rupture_risk_reported(self, mgr):
        mgr.update("agent-b", trust=0.1, intent=0.1)
        risk = mgr.rupture_risk("agent-b")
        assert risk > 0.0

    def test_manages_multiple_pairs_independently(self, mgr):
        mgr.update("agent-b", trust=0.9, intent=0.9, narrative=0.9, commitments=0.9)
        mgr.update("agent-c", trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)

        assert mgr.can_interact("agent-b") is True
        assert mgr.is_gated("agent-c") is True


class TestRuptureAndRepair:
    def test_gate_closes_on_rupture(self, mgr):
        mgr.update("agent-b", trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        assert mgr.is_gated("agent-b") is True
        assert mgr.can_interact("agent-b") is False

    def test_repair_releases_gate_when_primitives_recovered(self, mgr):
        mgr.update("agent-b", trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        assert mgr.is_gated("agent-b")

        mgr.update("agent-b", trust=0.9, intent=0.9, narrative=0.9, commitments=0.9)
        released = mgr.acknowledge_repair("agent-b")

        assert released is True
        assert mgr.can_interact("agent-b") is True

    def test_repair_fails_when_primitives_still_low(self, mgr):
        mgr.update("agent-b", trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        assert mgr.is_gated("agent-b")

        # Try to acknowledge repair without restoring primitives
        released = mgr.acknowledge_repair("agent-b")

        assert released is False
        assert mgr.is_gated("agent-b") is True

    def test_rupture_callback_fires(self, mgr):
        events = []
        mgr._on_rupture = lambda other_id, sig: events.append((other_id, sig))

        mgr.update("agent-b", trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)

        assert len(events) == 1
        other_id, sig = events[0]
        assert other_id == "agent-b"
        assert sig.signal_type == RUPTURE_DETECTED

    def test_repair_callback_fires(self, mgr):
        repair_events = []
        mgr._on_repair = lambda other_id, sig: repair_events.append((other_id, sig))

        mgr.update("agent-b", trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        mgr.update("agent-b", trust=0.9, intent=0.9, narrative=0.9, commitments=0.9)
        mgr.acknowledge_repair("agent-b")

        assert len(repair_events) == 1
        assert repair_events[0][0] == "agent-b"
        assert repair_events[0][1].signal_type == REPAIR_COMPLETE


class TestFleetView:
    def test_gated_empty_initially(self, mgr):
        mgr.update("agent-b", trust=0.9)
        assert mgr.gated() == []

    def test_gated_lists_blocked_relationships(self, mgr):
        mgr.update("agent-b", trust=0.9, intent=0.9, narrative=0.9, commitments=0.9)
        mgr.update("agent-c", trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        assert mgr.gated() == ["agent-c"]

    def test_at_risk_with_custom_threshold(self, mgr):
        mgr.update("agent-b", trust=0.9, intent=0.9, narrative=0.9, commitments=0.9)
        mgr.update("agent-c", trust=0.5, intent=0.5, narrative=0.5, commitments=0.5)
        # threshold=0.5: risk = (0.5+0.5+0.5+0.5)/4 = 0.5 → at risk
        at_risk = mgr.at_risk(threshold=0.5)
        assert "agent-c" in at_risk
        assert "agent-b" not in at_risk

    def test_healthy_excludes_gated_and_at_risk(self, mgr):
        mgr.update("agent-b", trust=0.9, intent=0.9, narrative=0.9, commitments=0.9)
        mgr.update("agent-c", trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        healthy = mgr.healthy()
        assert "agent-b" in healthy
        assert "agent-c" not in healthy

    def test_summary_counts(self, mgr):
        mgr.update("agent-b", trust=0.9, intent=0.9, narrative=0.9, commitments=0.9)
        mgr.update("agent-c", trust=0.1, intent=0.1, narrative=0.1, commitments=0.1)
        s = mgr.summary()
        assert s["relationships"] == 2
        assert s["gated"] == 1
        assert s["healthy"] == 1
        assert s["agent_id"] == "agent-a"


class TestPersistence:
    def test_history_logged_on_update(self, tmp_path):
        db = str(tmp_path / "test.db")
        mgr = RLP0Manager(agent_id="agent-a", db_path=db)
        mgr.update("agent-b", trust=0.9)
        mgr.update("agent-b", trust=0.7)

        history = mgr.history("agent-b")
        assert len(history) >= 2
        mgr.close()

    def test_state_survives_across_instances(self, tmp_path):
        db = str(tmp_path / "persist.db")

        mgr1 = RLP0Manager(agent_id="agent-a", db_path=db)
        mgr1.update("agent-b", trust=0.6, intent=0.6, narrative=0.6, commitments=0.6)
        mgr1.close()

        mgr2 = RLP0Manager(agent_id="agent-a", db_path=db)
        state = mgr2.state("agent-b")
        assert state.trust == pytest.approx(0.6)
        mgr2.close()
