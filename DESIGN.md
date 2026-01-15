# RLP-0 Design Principles

## Serve, Not Resolve

RLP-0 is committed to **serve**, not **resolve**.

### The Problem with Resolution

Most systems resolve tension:

```
Tension → Algorithm decides → Resolution → Drift → Capture
```

When systems resolve tensions automatically, they:
- Start with principles
- Drift over time
- Fail to notice deviation
- Get captured by power

### Tension-Holding

RLP-0 **maintains** tension instead of resolving it:

```
Tension → RLP-0 surfaces → Human/Agent chooses → Choice logged → Accountability
```

RLP-0 doesn't resolve the tension between:
- Individual benefit vs. collective coordination
- Efficiency vs. sovereignty
- Speed vs. safety
- Extraction vs. contribution

Instead, it:
- Makes trade-offs visible
- Surfaces when principles are being tested
- Requires explicit choices (not default drift)

## Multi-Mirror Self-Checking

RLP-0 encodes self-checking at the substrate level.

Each primitive has a built-in mirror:

| Primitive | Mirror |
|-----------|--------|
| **Trust** | Can be verified against behavior |
| **Intent** | Can be checked against action |
| **Narrative** | Can be tested for coherence |
| **Commitments** | Can be audited |

The architecture doesn't just hold relational state — it holds **self-accountable** relational state.

## Decision Point Checks

Decision points in expression protocols trigger RLP-0 state checks:

```
┌─────────────────────────────────────────┐
│           Decision Point                │
│  (coordinate / propagate / change)      │
└────────────────────┬────────────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │   RLP-0 State Check │
          │   ─────────────────  │
          │   "Does this serve   │
          │    [principle]?"     │
          └──────────┬──────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
   ┌─────────┐              ┌──────────┐
   │  YES    │              │  TENSION │
   │ proceed │              │ surfaced │
   └─────────┘              └────┬─────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Explicit choice      │
                     │  required + logged    │
                     └───────────────────────┘
```

Examples:
- Before agent coordination: *"Does this serve win/win?"*
- Before trust propagation: *"Does this maintain sovereignty?"*
- Before system change: *"Does this align with principles?"*

No silent trade-offs. No default drift.

## Anti-Drift Architecture

| Component | Function |
|-----------|----------|
| RLP-0 state | Continuous self-checking |
| Multi-mirror | Redundant feedback |
| Tension-holding | Prevents automatic drift |
| Context awareness | Learns from principle tests |

## Design Constraints

### Semantically Active, Operationally Minimal

RLP-0 can detect and signal, but cannot act.

**Yes:**
- Compute rupture_risk
- Emit RUPTURE_DETECTED
- Gate interactions
- Log choices

**No:**
- Perform repairs
- Make decisions
- Resolve tensions
- Speak for parties

### Layering Neutrality

RLP-0 is neutral about what counts as repair, trust, or alignment at the behavioral level.

Expression protocols (HX, AX, SX, GX...) define their own behavioral semantics. RLP-0 provides the substrate for relational state without prescribing how that state should be expressed.

### Storage Agnosticism

The semantic layer is independent of persistence implementation. RLP-0 can be instantiated over any storage layer without changing its meaning or operations.

---

## Summary

RLP-0 serves the relationship by refusing to make hard choices for you.

It surfaces tensions, requires explicit choices, and maintains accountability — without collapsing complexity into false resolution.

This is infrastructure for relationships that stay honest over time.
