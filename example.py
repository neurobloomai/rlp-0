"""
RLP-0 Example - Rupture Detection and Repair Flow

Demonstrates the MVK in action:
- Exchange damages trust
- RLP-0 detects rupture, emits signal, gates
- Expression protocol repairs
- RLP-0 releases gate
"""

from rlp_0 import RLP0, Signal


def main():
    print("=" * 60)
    print("RLP-0 Minimum Viable Kernel - Example")
    print("=" * 60)
    
    # Setup RLP-0 with signal handler
    def on_signal(signal: Signal):
        print(f"\n⚠️  SIGNAL: {signal}")
    
    rlp = RLP0(rupture_threshold=0.5)
    rlp.subscribe(on_signal)
    
    print("\n1. Initial state (healthy relationship)")
    print(f"   Trust: {rlp.state.trust}")
    print(f"   Intent: {rlp.state.intent}")
    print(f"   Narrative: {rlp.state.narrative}")
    print(f"   Commitments: {rlp.state.commitments}")
    print(f"   Rupture Risk: {rlp.rupture_risk}")
    print(f"   Gate Open: {rlp.check_gate()}")
    
    print("\n2. Exchange happens - trust and narrative are damaged...")
    rlp.update_state(trust=0.2, narrative=0.2, intent=0.3, commitments=0.3)
    
    print(f"\n   Trust: {rlp.state.trust}")
    print(f"   Narrative: {rlp.state.narrative}")
    print(f"   Rupture Risk: {rlp.rupture_risk:.2f}")
    print(f"   Gate Open: {rlp.check_gate()}")
    
    print("\n3. Interaction is blocked - repair required")
    if not rlp.check_gate():
        print("   ❌ Cannot proceed until repair")
    
    print("\n4. Expression protocol performs repair...")
    print("   (HX might apologize, AX might rollback policy)")
    rlp.update_state(trust=0.8, narrative=0.8, intent=0.8, commitments=0.8)
    
    print("\n5. Acknowledge repair")
    released = rlp.acknowledge_repair()
    print(f"   Gate released: {released}")
    print(f"   Gate Open: {rlp.check_gate()}")
    
    print("\n6. Final state")
    print(f"   Trust: {rlp.state.trust}")
    print(f"   Rupture Risk: {rlp.rupture_risk:.2f}")
    print(f"   ✅ Normal flow can resume")
    
    print("\n" + "=" * 60)
    print("Status Inspection")
    print("=" * 60)
    import json
    status = rlp.status()
    # Make it JSON serializable
    print(json.dumps(status, indent=2, default=str))


if __name__ == "__main__":
    main()
