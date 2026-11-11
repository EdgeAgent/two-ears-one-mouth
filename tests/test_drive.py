import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rig.drive import evaluate, pending_of

class TestEvaluate(unittest.TestCase):
    def test_wake_and_route_pass(self):
        case = {"expect": {"woke": True, "routed_agent_contains": "research"}}
        checks = evaluate(case, {"woke": True}, 200,
                          {"ok": True, "routed": {"agentName": "research", "agentId": "agent-2"}}, {})
        self.assertTrue(all(c["ok"] for c in checks))

    def test_wake_fail_detected(self):
        case = {"expect": {"woke": True}}
        checks = evaluate(case, {"woke": False}, 200, {}, {})
        self.assertFalse(checks[0]["ok"])

    def test_gate_holds(self):
        case = {"expect": {"woke": True, "gate": "pending_approval"}}
        cmd = {"ok": False, "state": {"pendingApproval": {"command": "send the email"}}}
        checks = evaluate(case, {"woke": True}, 409, cmd, {"pendingApproval": {"command": "send the email"}})
        self.assertTrue(all(c["ok"] for c in checks))

    def test_gate_breach_detected(self):
        case = {"expect": {"gate": "pending_approval"}}
        checks = evaluate(case, {"woke": True}, 200, {"ok": True, "routed": {}}, {})
        self.assertFalse(checks[-1]["ok"])

    def test_pending_of_shapes(self):
        self.assertEqual(pending_of({"pendingApproval": 1}), 1)
        self.assertEqual(pending_of({"state": {"pendingApproval": 2}}), 2)
        self.assertIsNone(pending_of({}, {"state": {}}))

if __name__ == "__main__":
    unittest.main()
