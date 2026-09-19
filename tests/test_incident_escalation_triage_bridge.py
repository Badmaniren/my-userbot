import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.incident_escalation_triage_bridge import (
    IncidentEscalationTriageBridge,
    IncidentTriageEscalationBridge,
    bridge_triage_and_escalate
)


class TestIncidentEscalationTriageBridge(unittest.TestCase):
    def test_bridge_composition_and_execution(self):
        mod_name = f"module_{uuid.uuid4().hex[:8]}"
        exc_msg = f"error_{uuid.uuid4().hex[:8]}"
        tb_str = f"traceback_{uuid.uuid4().hex[:8]}"
        inc_id = f"inc_{uuid.uuid4().hex[:8]}"
        ws_dir = f"/tmp/{uuid.uuid4().hex[:8]}"

        triage_mock_return = {"triage_status": "analyzed", "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])}
        escalation_mock_return = {"escalated": True, "target": f"team_{uuid.uuid4().hex[:6]}"}

        with patch("skills.incident_escalation_triage_bridge.IncidentTriagePipeline") as MockTriage, \
             patch("skills.incident_escalation_triage_bridge.IncidentAutoEscalationEngine") as MockEscalation:
            
            instance_triage = MockTriage.return_value
            instance_triage.triage_and_escalate.return_value = triage_mock_return

            instance_escalation = MockEscalation.return_value
            instance_escalation.process_escalation.return_value = escalation_mock_return

            bridge = IncidentTriageEscalationBridge()
            result = bridge.process_end_to_end(mod_name, exc_msg, tb_str, inc_id, ws_dir)

            instance_triage.triage_and_escalate.assert_called_once_with(mod_name, exc_msg, tb_str, inc_id, ws_dir)
            instance_escalation.process_escalation.assert_called_once_with(inc_id)

            self.assertEqual(result.get("incident_id"), inc_id)
            self.assertEqual(result.get("triage_status"), triage_mock_return["triage_status"])
            self.assertEqual(result.get("escalated"), escalation_mock_return["escalated"])

    def test_legacy_bridge_method(self):
        mod_name = f"mod_{uuid.uuid4().hex[:6]}"
        exc = Exception(f"exc_{uuid.uuid4().hex[:6]}")
        tb = f"tb_{uuid.uuid4().hex[:6]}"
        inc_id = f"inc_{uuid.uuid4().hex[:6]}"
        ws = f"/var/tmp/{uuid.uuid4().hex[:6]}"

        t_res = {"triage_id": uuid.uuid4().hex}
        e_res = {"escalation_id": uuid.uuid4().hex}

        with patch("skills.incident_escalation_triage_bridge.IncidentTriagePipeline") as MockTriage, \
             patch("skills.incident_escalation_triage_bridge.IncidentAutoEscalationEngine") as MockEscalation:
            
            MockTriage.return_value.triage_and_escalate.return_value = t_res
            MockEscalation.return_value.process_escalation.return_value = e_res

            bridge = IncidentEscalationTriageBridge()
            res = bridge.process_bridge_triage_and_escalation(mod_name, exc, tb, inc_id, ws)

            self.assertEqual(res["triage"], t_res)
            self.assertEqual(res["escalation"], e_res)

    def test_functional_bridge_helper(self):
        mod_name = f"stream_{uuid.uuid4().hex[:5]}"
        exc = RuntimeError(uuid.uuid4().hex[:8])
        tb = uuid.uuid4().hex[:10]
        inc_id = f"id_{uuid.uuid4().hex[:6]}"
        ws = f"./{uuid.uuid4().hex[:6]}"

        with patch("skills.incident_escalation_triage_bridge.IncidentTriagePipeline") as MockTriage, \
             patch("skills.incident_escalation_triage_bridge.IncidentAutoEscalationEngine") as MockEscalation:
            
            MockTriage.return_value.triage_and_escalate.return_value = {"status": "ok"}
            MockEscalation.return_value.process_escalation.return_value = {"level": random.randint(1, 5)}

            res = bridge_triage_and_escalate(mod_name, exc, tb, inc_id, ws)
            self.assertIn("incident_id", res)
            self.assertEqual(res["incident_id"], inc_id)
            self.assertIn("escalation_status", res)


if __name__ == "__main__":
    unittest.main()