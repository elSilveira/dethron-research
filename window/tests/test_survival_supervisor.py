import unittest
from survival_supervisor import reconcile


class Node:
    def __init__(self, slot, alive=True):
        self.slot, self.alive = slot, alive
        self.address = f"127.0.0.1:{10000 + slot}"
        self.hello = {"pid": slot + 1, "node_id": f"identity-{slot}"}

    def health(self):
        if not self.alive:
            raise OSError("connection refused")
        return self.hello


class SupervisorTests(unittest.TestCase):
    def test_detects_dead_service_and_repairs_from_live_donor(self):
        nodes = [Node(0), Node(1, False), Node(2, False)]
        calls = []
        def spawn(slot):
            calls.append(("spawn", slot))
            return Node(slot)
        def repair(donors, targets):
            calls.append(("repair", donors, targets))
            return {"verified_targets": len(targets)}
        updated, event = reconcile(nodes, spawn, repair)
        self.assertEqual(len(updated), 3)
        self.assertEqual(event["failed_slots"], [1, 2])
        self.assertEqual(calls[-1], ("repair", [nodes[0].address], [n.address for n in updated[1:]]))

    def test_no_survivor_and_failed_readback_cannot_claim_repaired(self):
        with self.assertRaisesRegex(ValueError, "survivor"):
            reconcile([Node(0, False)], lambda slot: self.fail("must not spawn"), lambda a, b: {})
        with self.assertRaisesRegex(ValueError, "readback"):
            reconcile([Node(0), Node(1, False)], Node, lambda a, b: {"verified_targets": 0})

    def test_healthy_network_does_not_rewrite_storage(self):
        nodes = [Node(0)]
        updated, event = reconcile(nodes, lambda s: self.fail(), lambda a, b: self.fail())
        self.assertEqual(updated, nodes)
        self.assertEqual(event["failed_slots"], [])
