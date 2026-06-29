# RLP-0

**Relational Ledger Protocol - Zero**

The substrate layer for relational infrastructure. RLP-0 defines what it means for a relationship to exist computationally — and tracks when that relationship breaks down.

---

## What it is

RLP-0 is not a database. Not a spec. Not an abstraction.

It is a **state primitive** that tracks four relational signals — and detects when their breakdown crosses into rupture.

| Primitive | Signal |
|---|---|
| **trust** | Confidence |
| **intent** | Direction |
| **narrative** | Coherence |
| **commitments** | Accountability |

When those signals degrade past a threshold, RLP-0 detects rupture, closes a gate, and emits `RUPTURE_DETECTED`. It does not repair. That is the expression layer's job. RLP-0 senses and signals — it does not decide or act.

---

## Quick start

```python
from rlp_0 import RLP0, Signal

rlp = RLP0(rupture_threshold=0.5)

def on_signal(signal: Signal):
    print(f"Signal: {signal}")

rlp.subscribe(on_signal)

# Exchange damages trust and narrative
rlp.update_state(trust=0.2, narrative=0.2, intent=0.3, commitments=0.3)
# Signal: [RUPTURE_DETECTED] risk=0.55 at ...

print(rlp.is_gated)      # True — gate closed until repair
print(rlp.check_gate())  # False — cannot proceed

# Expression protocol performs repair (HX apologizes, AX rolls back, GX votes)
rlp.update_state(trust=0.85, narrative=0.85, intent=0.8, commitments=0.8)

released = rlp.acknowledge_repair()
# Signal: [REPAIR_COMPLETE] risk=0.08 at ...

print(released)          # True — gate released
print(rlp.check_gate())  # True — flow can resume
```

`acknowledge_repair()` validates that primitives actually improved. If risk is still above threshold, the gate stays closed.

---

## Managing multiple relationships

`RLP0Manager` tracks N relationships from a single agent — persistence, callbacks, fleet visibility:

```python
from rlp_0 import RLP0Manager

mgr = RLP0Manager(
    agent_id          = "agent-a",
    rupture_threshold = 0.5,
    db_path           = "rlp.db",          # persists across restarts
    on_rupture = lambda other_id, sig: print(f"Rupture with {other_id}"),
    on_repair  = lambda other_id, sig: print(f"Repaired with {other_id}"),
)

# After an exchange
mgr.update("agent-b", trust=0.9, intent=0.85)
mgr.update("agent-c", trust=0.2, intent=0.2, narrative=0.1, commitments=0.1)

# Check before acting
if not mgr.can_interact("agent-c"):
    print("blocked — repair required")

# Fleet view
print(mgr.gated())     # ["agent-c"]
print(mgr.at_risk())   # ["agent-c"]
print(mgr.summary())
# {"agent_id": "agent-a", "relationships": 2, "gated": 1, "healthy": 1, ...}

# State change history
for entry in mgr.history("agent-c"):
    print(entry["recorded_at"], entry["trust"], entry["rupture_risk"])
```

---

## Persistence

`RelationalStorage` is the storage layer — SQLite-backed, storage-agnostic in design:

```python
from rlp_0 import RelationalStorage, RelationalState

storage = RelationalStorage("rlp.db")

# Save
storage.save("agent-a", "agent-b", state)

# Load current state
state = storage.load("agent-a", "agent-b")

# Audit trail — append-only history
history = storage.history("agent-a", "agent-b", limit=20)

# Fleet queries
gated  = storage.gated_pairs()                 # [(from_id, to_id), ...]
at_risk = storage.at_risk_pairs(threshold=0.5) # [(from_id, to_id), ...]
```

---

## Three-layer architecture

```
┌─────────────────────────────────────────────────┐
│   PACT-HX  /  PACT-AX  /  PACT-GX  /  ...      │  Expression Protocols
└──────────────────────┬──────────────────────────┘
                       │
                 write ▼▲ read
          ┌────────────────────────┐
          │  Protocol / RLP0       │ ◄──── GATE (blocks until repair)
          │    update_state()      │
          │    acknowledge_repair()│
          └────────────┬───────────┘
                       │▲ SIGNAL (RUPTURE_DETECTED / REPAIR_COMPLETE)
                       ▼│
        ╔══════════════╧══════════════╗
        ║    SEMANTIC (RelationalState)║
        ║  trust · intent             ║
        ║  narrative · commitments    ║  ← Active sensing
        ║  rupture_risk (computed)    ║
        ╚══════════════╤══════════════╝
                       │
               persist ▼▲ retrieve
          ┌────────────┴───────────┐
          │ RelationalStorage      │
          │  (SQLite — swappable)  │
          └────────────────────────┘
```

RLP-0 is storage-agnostic. Any backend — graph DB, distributed ledger, file system — can replace `RelationalStorage` without changing RLP-0's meaning.

---

## Relationship to PACT

RLP-0 is the substrate. Expression protocols consume it:

```
[ PACT-HX ]   [ PACT-AX ]   [ PACT-GX ]   [ Future protocols ]
      \              |              |               /
       \             |              |              /
        ────────── RLP-0 ──────────────────────
```

Same substrate. Different grammars. PACT-HX reinterprets the four primitives for human relationships. PACT-AX for agent coordination. PACT-GX for collective authority.

---

## Development

```bash
git clone https://github.com/neurobloomai/rlp-0
cd rlp-0
pip install -e ".[dev]"
pytest tests/ -v    # 46 tests
```

---

## Documentation

- [SPEC.md](SPEC.md) — technical architecture and three-layer model
- [DESIGN.md](DESIGN.md) — design principles (tension-holding, anti-drift)

---

## License

MIT — built by the [neurobloom.ai](https://neurobloom.ai) community.
