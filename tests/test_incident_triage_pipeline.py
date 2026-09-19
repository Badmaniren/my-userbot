import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_triage_pipeline import IncidentTriagePipeline


class TestIncidentTriagePipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = IncidentTriagePipeline()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_exc = Exception(''.join(random.choices(string.ascii_letters, k=15)))
        self.random_trace = ''.join(random.choices(string.ascii_letters + string.whitespace, k=30))
        self.random_incident_id = uuid.uuid4().hex
        self.random_workspace = '/' + ''.join(random.choices(string.ascii_lowercase, k=8))

    def test_triage_pipeline_high_severity_escalation(self):
        eval_result = {
            "severity": "CRITICAL",
            "score": random.randint(90, 100),
            "incident_id": self.random_incident_id
        }
        escalation_result = {
            "status": "escalated",
            "handler": ''.join(random.choices(string.ascii_lowercase, k=6)),
            "target": self.random_incident_id
        }

        with patch('skills.incident_triage_pipeline.incident_severity_evaluator.evaluate_incident_severity') as mock_eval, \
             patch('skills.incident_triage_pipeline.incident_auto_escalation_engine.auto_escalate_incident') as mock_escalate:

            mock_eval.return_value = eval_result
            mock_escalate.return_value = escalation_result

            result = self.pipeline.triage_and_escalate(
                module_name=self.random_module,
                exception=self.random_exc,
                traceback_str=self.random_trace,
                incident_id=self.random_incident_id,
                workspace_dir=self.random_workspace
            )

            mock_eval.assert_called_once_with(
                self.random_module,
                self.random_exc,
                self.random_trace,
                self.random_incident_id
            )
            mock_escalate.assert_called_once_with(
                self.random_incident_id,
                eval_result["severity"],
                self.random_workspace
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), self.random_incident_id)
            self.assertEqual(result.get("severity"), "CRITICAL")
            self.assertEqual(result.get("escalation_status"), "escalated")

    def test_triage_pipeline_low_severity_no_escalation(self):
        eval_result = {
            "severity": "LOW",
            "score": random.randint(1, 30),
            "incident_id": self.random_incident_id
        }

        with patch('skills.incident_triage_pipeline.incident_severity_evaluator.evaluate_incident_severity') as mock_eval, \
             patch('skills.incident_triage_pipeline.incident_auto_escalation_engine.auto_escalate_incident') as mock_escalate:

            mock_eval.return_value = eval_result

            result = self.pipeline.triage_and_escalate(
                module_name=self.random_module,
                exception=self.random_exc,
                traceback_str=self.random_trace,
                incident_id=self.random_incident_id,
                workspace_dir=self.random_workspace
            )

            mock_eval.assert_called_once_with(
                self.random_module,
                self.random_exc,
                self.random_trace,
                self.random_incident_id
            )
            mock_escalate.assert_not_called()

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), self.random_incident_id)
            self.assertEqual(result.get("severity"), "LOW")
            self.assertNotIn("escalation_status", result)

    def test_triage_pipeline_stream_evaluation(self):
        random_stream_data = io.BytesIO(uuid.uuid4().bytes + random.randbytes(16))
        stream_eval_result = {
            "severity": "HIGH",
            "anomaly_detected": True,
            "metrics": random.randint(50, 500)
        }

        with patch('skills.incident_triage_pipeline.IncidentSeverityEvaluator') as MockEvaluatorClass, \
             patch('skills.incident_triage_pipeline.IncidentAutoEscalationEngine') as MockEscalationClass:

            evaluator_instance = MockEvaluatorClass.return_value
            evaluator_instance.evaluate_stream.return_value = stream_eval_result

            escalation_instance = MockEscalationClass.return_value
            escalation_instance.process_escalation.return_value = {"routed": True}

            result = self.pipeline.triage_stream(
                module_name=self.random_module,
                stream_data=random_stream_data,
                incident_id=self.random_incident_id
            )

            evaluator_instance.evaluate_stream.assert_called_once_with(
                self.random_module,
                random_stream_data
            )
            escalation_instance.process_escalation.assert_called_once_with(self.random_incident_id)

            self.assertEqual(result.get("severity"), "HIGH")
            self.assertTrue(result.get("escalation_triggered"))


if __name__ == '__main__':
    unittest.main()