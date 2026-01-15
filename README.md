# RLP-0

**Relational Ledger Protocol - Zero**

RLP-0 is a minimal state primitive for relational infrastructure. It defines what it means for a relationship to exist computationally.

## What RLP-0 Is

RLP-0 is not a database. Not just a spec. Not just an abstraction.

It is a **state primitive** that exists in three layers simultaneously:

- **Semantic Layer** — what a relationship means
- **Protocol Layer** — how relationship state is read/written
- **Storage Layer** — where relationship state lives

## Four Primitives

RLP-0 tracks relational state through four primitives:

| Primitive | Signal |
|-----------|--------|
| **Trust** | Confidence |
| **Intent** | Direction |
| **Narrative** | Coherence |
| **Commitments** | Accountability |

## Active Substrate

RLP-0 is semantically active but operationally minimal.

It can detect rupture and emit relational signals, but it does not perform expression or behavior. It **nudges upward**; it doesn't **speak upward**.

Signals and gates, not speech and action.

## Relationship to PACT

RLP-0 is protocol-agnostic relational infrastructure.

Expression protocols consume RLP-0 as a dependency:

```
[ PACT-HX ]     [ PACT-AX ]     [ Future Protocols ]
     \              |               /
      \             |              /
       \            |             /
        ─────── RLP-0 ───────
```

- **PACT-HX** = human expression protocol over RLP-0
- **PACT-AX** = agent coordination protocol over RLP-0
- **PACT-SX, EX, GX...** = future expression protocols

Same substrate. Different grammars.

## Documentation

- [SPEC.md](SPEC.md) — Technical architecture
- [DESIGN.md](DESIGN.md) — Design principles

## License

MIT

---

Part of [NeuroBloom](https://neurobloom.ai) infrastructure.
