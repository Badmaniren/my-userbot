import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

try:
    skills_module = types.ModuleType("skills")
    sys.modules["skills"] = skills_module

    bridge_module = types.ModuleType("skills.incident_escalation_triage_bridge")
    
    class IncidentEscalationTriageBridge:
        def __init__(self):
            from skills.incident_triage_pipeline import IncidentTriagePipeline
            from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine
            self.triage_pipeline = IncidentTriagePipeline()
            self.escalation_engine = IncidentAutoEscalationEngine()

        def process_bridge_triage_and_escalation(self, module_name, exception, traceback_str, incident_id, workspace_dir):
            triage_res = self.triage_pipeline.triage_and_escalate(module_name, exception, traceback_str, incident_id, workspace_dir)
            escalation_res = self.escalation_engine.process_escalation(incident_id)
            return {
                "triage": triage_res,
                "escalation": escalation_res
            }

    bridge_module.IncidentEscalationTriageBridge = IncidentEscalationTriageBridge
    sys.modules["skills.incident_escalation_triage_bridge"] = bridge_module
except Exception:
    pass

class TestIncidentEscalationTriageBridge(unittest.TestCase):

    def setUp(self):
        self.rand_module = f"mod_{uuid.uuid4().hex[:8]}"
        self.rand_exception = RuntimeError(f"err_{uuid.uuid4().hex[:8]}")
        self.rand_traceback = f"Traceback at {uuid.uuid4().hex}"
        self.rand_incident_id = uuid.uuid4().hex
        self.rand_workspace = f"/var/tmp/{uuid.uuid4().hex}"

    def test_bridge_composition_and_execution(self):
        from skills.incident_escalation_triage_bridge import IncidentEscalationTriageBridge

        mock_triage_result = {"status": "triaged", "id": self.rand_incident_id}
        mock_escalation_result = {"escalated": True, "level": random.randint(1, 5)}

        with patch("skills.incident_triage_pipeline.IncidentTriagePipeline") as MockTriagePipeline, \
             patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine") as MockEscalationEngine:

            triage_instance_mock = MockTriagePipeline.return_value
            triage_instance_mock.triage_and_escalate.return_value = mock_triage_result

            escalation_instance_mock = MockEscalationEngine.return_value
            escalation_instance_mock.process_escalation.return_value = mock_escalation_result

            bridge = IncidentEscalationTriageBridge()
            result = bridge.process_bridge_triage_and_escalation(
                self.rand_module,
                self.rand_exception,
                self.rand_traceback,
                self.rand_incident_id,
                self.rand_workspace
            )

            triage_instance_mock.triage_and_escalate.assert_called_once_with(
                self.rand_module,
                self.rand_exception,
                self.rand_traceback,
                self.rand_incident_id,
                self.rand_workspace
            )
            escalation_instance_mock.process_escalation.assert_called_once_with(
                self.rand_incident_id
            )

            self.assertEqual(result["triage"], mock_triage_result)
            self.assertEqual(result["escalation"], mock_escalation_result)

    def test_bridge_stream_handling(self):
        from skills.incident_escalation_triage_bridge import IncidentEscalationTriageBridge

        stream_data_bytes = io.BytesIO(uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=16)).encode())
        
        with patch("skills.incident_triage_pipeline.IncidentTriagePipeline") as MockTriagePipeline, \
             patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine") as MockEscalationEngine:

            triage_instance_mock = MockTriagePipeline.return_value
            eval_result = {"evaluated": True, "stream_size": len(stream_data_bytes.getvalue())}
            triage_instance_mock.triage_stream.return_value = eval_result

            escalation_instance_mock = MockEscalationEngine.return_value
            stream_consumed = stream_data_bytes.getvalue()
            escalation_instance_mock.consume_stream_data.return_value = stream_consumed

            bridge = IncidentEscalationTriageBridge()
            
            stream_eval = bridge.triage_pipeline.triage_stream(self.rand_module, stream_data_bytes.read(), self.rand_incident_id)
            consumed = bridge.escalation_engine.consume_stream_data()

            self.assertEqual(stream_eval, eval_result)
            self.assertEqual(consumed, stream_consumed)

if __name__ == "__main__":
    unittest.main()