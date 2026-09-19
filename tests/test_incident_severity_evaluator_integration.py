import unittest
import uuid
import random
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.incident_aggregator import IncidentAggregator
from skills.notification_template_engine import NotificationTemplateEngine
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine

class TestIncidentSeverityEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = IncidentAggregator()
        self.template_engine = NotificationTemplateEngine()
        self.escalation_engine = IncidentAutoEscalationEngine()
        self.evaluator = IncidentSeverityEvaluator(
            aggregator=self.aggregator,
            template_engine=self.template_engine
        )

    def test_end_to_end_evaluation_and_escalation(self):
        random_id = f"inc-{uuid.uuid4()}"
        module_name = f"module_{uuid.uuid4().hex[:6]}"
        error_msg = f"Critical failure test {uuid.uuid4()}"
        exc = RuntimeError(error_msg)
        tb_str = "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise RuntimeError()"

        result = self.evaluator.evaluate(
            module_name=module_name,
            exception=exc,
            traceback_str=tb_str,
            incident_id=random_id
        )

        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], random_id)
        self.assertIn("severity", result)
        self.assertIn("payload", result)
        self.assertIn("aggregated_data", result)

        severity = result["severity"]
        self.assertIn(severity, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        escalation_result = self.escalation_engine.process_escalation(
            incident_id=random_id,
            severity=severity,
            context=result["aggregated_data"]
        )

        self.assertIsNotNone(escalation_result)
        if isinstance(escalation_result, dict):
            self.assertEqual(escalation_result.get("incident_id"), random_id)

    def test_evaluate_stream_with_random_metrics(self):
        stream_id = f"stream-{uuid.uuid4()}"
        freq = random.randint(1, 100)
        stream_data = {
            "incident_id": stream_id,
            "frequency": freq,
            "message": f"Stream log error {uuid.uuid4()}"
        }

        result = self.evaluator.evaluate_stream(
            module_name=f"stream_mod_{uuid.uuid4().hex[:4]}",
            stream_data=stream_data
        )

        self.assertEqual(result["incident_id"], stream_id)
        if freq >= 50:
            self.assertEqual(result["severity"], "CRITICAL")
        elif freq >= 26:
            self.assertEqual(result["severity"], "HIGH")
        elif freq >= 6:
            self.assertEqual(result["severity"], "MEDIUM")
        else:
            self.assertEqual(result["severity"], "LOW")

if __name__ == "__main__":
    unittest.main()