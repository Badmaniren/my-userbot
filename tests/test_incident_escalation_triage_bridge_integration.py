import unittest
import uuid
import tempfile
import os
from skills.incident_escalation_triage_bridge import (
    IncidentEscalationTriageBridge,
    IncidentTriageEscalationBridge,
    bridge_triage_and_escalate
)


class TestIncidentEscalationTriageBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.incident_id = f"inc-{uuid.uuid4()}"
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.exception = RuntimeError(f"Test failure {uuid.uuid4()}")
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line 1, in <module>\n    raise {self.exception}"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_incident_escalation_triage_bridge_class(self):
        bridge = IncidentEscalationTriageBridge()
        result = bridge.process_bridge_triage_and_escalation(
            self.module_name,
            self.exception,
            self.traceback_str,
            self.incident_id,
            self.workspace_dir
        )
        self.assertIsInstance(result, dict)
        self.assertIn("triage", result)
        self.assertIn("escalation", result)

    def test_incident_triage_escalation_bridge_class_end_to_end(self):
        bridge = IncidentTriageEscalationBridge()
        result = bridge.process_end_to_end(
            self.module_name,
            self.exception,
            self.traceback_str,
            self.incident_id,
            self.workspace_dir
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.incident_id)
        self.assertIn("escalation_status", result)

    def test_bridge_triage_and_escalate_function(self):
        result = bridge_triage_and_escalate(
            self.module_name,
            self.exception,
            self.traceback_str,
            self.incident_id,
            self.workspace_dir
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.incident_id)
        self.assertIn("escalation_status", result)


if __name__ == "__main__":
    unittest.main()