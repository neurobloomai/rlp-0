# RLP-0 Specification

## Overview

RLP-0 (Relational Ledger Protocol - Zero) is the minimal protocol instantiation of shared relational state.

```
NeuroBloom Substrate
└── Shared Relational State (concept)
    └── RLP-0 (minimal protocol instantiation)
        └── Relational Ledger
            └── trust, intent, narrative, commitments
```

## Architecture

### Three-Layer Model

RLP-0 exists in three layers simultaneously:

```
┌─────────────────────────────────────────────────┐
│     PACT-HX  /  PACT-AX  /  PACT-SX / ...       │  Expression Protocols
└──────────────────────┬──────────────────────────┘
                       │
                 write ▼▲ read
          ┌────────────────────────┐
          │  Protocol/Operations   │ ◄──── GATE (blocks until repair)
          │    (read/write API)    │
          └────────────┬───────────┘
                       │▲ SIGNAL (rupture_detected)
                       ▼│
        ╔══════════════╧══════════════╗
        ║         SEMANTIC            ║
        ║   trust, intent,            ║
        ║   narrative, commitments    ║
        ║   ─────────────────────     ║
        ║   rupture_risk (computed)   ║  ← Active sensing
        ╚══════════════╤══════════════╝
                       │
               persist ▼▲ retrieve
          ┌────────────┴───────────┐
          │        Storage         │
          │   (persistence API)    │
          └────────────┬───────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│      DB  /  Graph  /  Ledger  /  File           │  Persistence Layer
└─────────────────────────────────────────────────┘
```

### Layer Definitions

| Layer | Function | Interface |
|-------|----------|-----------|
| **Semantic** | Core of RLP-0. Defines what relationship means. | — |
| **Protocol** | Operations interface. How state is read/written. | Upward to expression protocols |
| **Storage** | Persistence interface. Where state lives. | Downward to concrete storage |

### Four Primitives

The semantic layer tracks relational state through four primitives:

| Primitive | Signal | Description |
|-----------|--------|-------------|
| `trust` | Confidence | The confidence signal between parties |
| `intent` | Direction | The directional signal of purpose |
| `narrative` | Coherence | The coherence signal of shared understanding |
| `commitments` | Accountability | The accountability signal of promises made |

## Active Substrate

RLP-0 is **semantically active but operationally minimal**.

### Signals

RLP-0 can emit signals upward to expression protocols:

- `RUPTURE_DETECTED` — relational coherence has broken down

### Gates

RLP-0 can control flow through gates:

- `gate()` — blocks interaction until condition met
- `release()` — allows interaction to resume

### Principle

**Active signaling, not active acting.**

RLP-0 senses and signals, but does not decide how to respond. That is the expression layer's job.

## Rupture Flow

```
1. Exchange happens
         │
         ▼
2. RLP-0: compute_rupture_risk()
         │
         ▼ threshold crossed
3. RLP-0: emit(RUPTURE_DETECTED)
         │
         ▼
4. RLP-0: gate()
         │
         ▼
5. HX/AX: [blocked - must repair]
         │
         ▼
6. HX/AX: performs repair (protocol-specific)
         │
         ▼
7. HX/AX: calls acknowledge_repair()
         │
         ▼
8. RLP-0: validates, updates state, release()
         │
         ▼
9. Normal flow resumes
```

### Repair Semantics

Repair is a **behavioral action** in HX/AX, **acknowledged** by RLP-0.

- HX/AX performs the repair (words/actions)
- RLP-0 only validates that repair occurred and releases the gate

This preserves layering and neutrality. RLP-0 doesn't know if repair was an apology (HX), a policy rollback (AX), or a governance vote (GX). It just knows: repair was claimed, validated, gate released.

## Minimum Viable Kernel (MVK)

The smallest viable implementation of RLP-0:

```
┌─────────────────────────────────┐
│         MVK Scope               │
├─────────────────────────────────┤
│  State:                         │
│    • rupture_risk (float)       │
│                                 │
│  Signals:                       │
│    • RUPTURE_DETECTED           │
│                                 │
│  Gates:                         │
│    • block_until_repair()       │
│    • release()                  │
│                                 │
│  Operations:                    │
│    • compute_rupture_risk()     │
│    • acknowledge_repair()       │
└─────────────────────────────────┘
```

## Storage Agnosticism

RLP-0 is storage-agnostic. The persistence layer can be:

- Relational database
- Graph database
- Distributed ledger
- File system
- In-memory store

The semantic layer remains constant regardless of storage implementation.
