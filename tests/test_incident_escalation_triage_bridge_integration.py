import unittest
import uuid
import random
import os
import tempfile
from skills.incident_escalation_triage_bridge import (
    IncidentTriageEscalationBridge,
    bridge_triage_and_escalate
)
from skills.incident_triage_pipeline import IncidentTriagePipeline
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine


class TestIncidentEscalationTriageBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.incident_id = f"inc-{uuid.uuid4()}"
        self.module_name = f"module_{random.randint(1000, 9999)}"
        self.exception_msg = f"CriticalSystemFailure_{uuid.uuid4()}"
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 100)}\nException: {self.exception_msg}"

    def tearDown(self):
        self.workspace.cleanup()

    def test_end_to_end_triage_and_escalation_composition(self):
        pipeline = IncidentTriagePipeline()
        engine = IncidentAutoEscalationEngine()
        
        self.assertIsNotNone(pipeline)
        self.assertIsNotNone(engine)

        result = bridge_triage_and_escalate(
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            traceback_str=self.traceback_str,
            incident_id=self.incident_id,
            workspace_dir=self.workspace.name
        )

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("escalation_status", result)

        escalation_response = engine.process_escalation(self.incident_id)
        self.assertIsInstance(escalation_response, dict)
        self.assertIn("incident_id", escalation_response)

    def test_bridge_class_direct_execution(self):
        bridge_instance = IncidentTriageEscalationBridge()
        self.assertTrue(hasattr(bridge_instance, "process_end_to_end"))

        execution_result = bridge_instance.process_end_to_end(
            module_name=self.module_name,
            exception=ValueError(self.exception_msg),
            traceback_str=self.traceback_str,
            incident_id=self.incident_id,
            workspace_dir=self.workspace.name
        )

        self.assertIsInstance(execution_result, dict)
        self.assertEqual(execution_result.get("incident_id"), self.incident_id)


if __name__ == "__main__":
    unittest.main()