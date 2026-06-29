"""
Tests for RLP-0 storage layer.
"""
import pytest
from datetime import datetime, timezone
from rlp_0 import RelationalState, RelationalStorage


@pytest.fixture
def store(tmp_path):
    s = RelationalStorage(str(tmp_path / "test.db"))
    yield s
    s.close()


@pytest.fixture
def state():
    return RelationalState(trust=0.8, intent=0.7, narrative=0.9, commitments=0.6)


class TestSaveLoad:
    def test_load_nonexistent_returns_none(self, store):
        assert store.load("a", "b") is None

    def test_save_and_load_round_trips(self, store, state):
        store.save("a", "b", state)
        loaded = store.load("a", "b")
        assert loaded is not None
        assert loaded.trust       == pytest.approx(state.trust)
        assert loaded.intent      == pytest.approx(state.intent)
        assert loaded.narrative   == pytest.approx(state.narrative)
        assert loaded.commitments == pytest.approx(state.commitments)

    def test_save_upserts_existing_pair(self, store, state):
        store.save("a", "b", state)
        updated = RelationalState(trust=0.5, intent=0.5, narrative=0.5, commitments=0.5)
        store.save("a", "b", updated)
        loaded = store.load("a", "b")
        assert loaded.trust == pytest.approx(0.5)

    def test_save_persists_gated_flag(self, store):
        gated_state = RelationalState(is_gated=True, rupture_risk=0.8)
        store.save("a", "b", gated_state)
        loaded = store.load("a", "b")
        assert loaded.is_gated is True

    def test_pairs_are_directional(self, store, state):
        store.save("a", "b", state)
        assert store.load("b", "a") is None


class TestHistory:
    def test_history_empty_for_unknown_pair(self, store):
        assert store.history("x", "y") == []

    def test_history_accumulates_on_each_save(self, store, state):
        store.save("a", "b", state)
        store.save("a", "b", state.update(trust=0.5))
        history = store.history("a", "b")
        assert len(history) == 2

    def test_history_newest_first(self, store, state):
        store.save("a", "b", state)
        store.save("a", "b", state.update(trust=0.3))
        history = store.history("a", "b")
        # Newest first — most recent save had trust=0.3
        assert history[0]["trust"] == pytest.approx(0.3)

    def test_history_respects_limit(self, store, state):
        for i in range(10):
            store.save("a", "b", state.update(trust=i / 10))
        history = store.history("a", "b", limit=3)
        assert len(history) == 3

    def test_history_change_type_recorded(self, store, state):
        store.save("a", "b", state, change_type="rupture_detected")
        history = store.history("a", "b")
        assert history[0]["change_type"] == "rupture_detected"


class TestFleetQueries:
    def test_all_pairs_empty(self, store):
        assert store.all_pairs() == []

    def test_all_pairs_returns_saved_pairs(self, store, state):
        store.save("a", "b", state)
        store.save("a", "c", state)
        pairs = store.all_pairs()
        assert ("a", "b") in pairs
        assert ("a", "c") in pairs

    def test_gated_pairs(self, store):
        store.save("a", "b", RelationalState(is_gated=False))
        store.save("a", "c", RelationalState(is_gated=True, rupture_risk=0.9))
        assert store.gated_pairs() == [("a", "c")]

    def test_at_risk_pairs(self, store):
        store.save("a", "b", RelationalState(rupture_risk=0.3))
        store.save("a", "c", RelationalState(rupture_risk=0.8))
        at_risk = store.at_risk_pairs(threshold=0.5)
        assert ("a", "c") in at_risk
        assert ("a", "b") not in at_risk

    def test_delete_removes_pair_and_history(self, store, state):
        store.save("a", "b", state)
        assert store.delete("a", "b") is True
        assert store.load("a", "b") is None
        assert store.history("a", "b") == []

    def test_delete_returns_false_for_unknown(self, store):
        assert store.delete("ghost", "nobody") is False


class TestInMemory:
    def test_in_memory_store_works(self):
        s = RelationalStorage(":memory:")
        state = RelationalState(trust=0.7)
        s.save("a", "b", state)
        assert s.load("a", "b").trust == pytest.approx(0.7)
