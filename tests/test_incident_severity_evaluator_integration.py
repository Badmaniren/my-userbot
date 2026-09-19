import unittest
import uuid
import random
from skills.incident_severity_evaluator import IncidentSeverityEvaluator, evaluate_incident_severity
from skills.incident_aggregator import IncidentAggregator
from skills.notification_template_engine import NotificationTemplateEngine

class TestIncidentSeverityEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = IncidentAggregator()
        self.template_engine = NotificationTemplateEngine()
        self.evaluator = IncidentSeverityEvaluator(
            aggregator=self.aggregator,
            template_engine=self.template_engine
        )

    def test_evaluate_end_to_end_flow(self):
        random_id = f"inc-{uuid.uuid4()}"
        module_name = f"module_{random.randint(1000, 9999)}"
        exception_msg = f"Critical error in system {random.randint(1, 100)}"
        exc = RuntimeError(exception_msg)
        traceback_str = "Traceback (most recent call last):\n  File 'test.py', line 10, in <module>\n    raise RuntimeError()"

        result = self.evaluator.evaluate(
            module_name=module_name,
            exception=exc,
            traceback_str=traceback_str,
            incident_id=random_id
        )

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertIn("severity", result)
        self.assertIn("payload", result)
        self.assertIn("aggregated_data", result)
        
        self.assertEqual(result["incident_id"], random_id)
        self.assertIn(result["severity"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_functional_helper_wrapper(self):
        random_id = f"inc-func-{uuid.uuid4()}"
        module_name = f"mod_func_{random.randint(100, 999)}"
        exc = ValueError("Invalid operational state")
        traceback_str = "Traceback: value error occurred"

        result = evaluate_incident_severity(
            module_name=module_name,
            exception=exc,
            traceback_str=traceback_str,
            incident_id=random_id
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["incident_id"], random_id)
        self.assertIsNotNone(result["severity"])

    def test_evaluate_stream_processing(self):
        random_id = f"stream-{uuid.uuid4()}"
        frequency = random.randint(1, 60)
        stream_data = {
            "parsed_id": random_id,
            "frequency": frequency,
            "stream_source": "telemetry_gateway"
        }

        result = self.evaluator.evaluate_stream(
            module_name="telemetry_streamer",
            stream_data=stream_data
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["incident_id"], random_id)
        
        if frequency >= 50:
            self.assertEqual(result["severity"], "CRITICAL")
        elif frequency >= 26:
            self.assertEqual(result["severity"], "HIGH")
        elif frequency >= 6:
            self.assertEqual(result["severity"], "MEDIUM")
        else:
            self.assertEqual(result["severity"], "LOW")

    def test_evaluate_and_notify_integration(self):
        random_id = f"notif-{uuid.uuid4()}"
        module_name = f"auth_module_{random.randint(1, 50)}"
        exc = SystemError("Fatal subsystem failure")
        traceback_str = "Traceback: system error"

        result = self.evaluator.evaluate_and_notify(
            module_name=module_name,
            exception=exc,
            traceback_str=traceback_str,
            incident_id=random_id
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["incident_id"], random_id)
        self.assertIn("notification", result)
        self.assertIn("payload", result)
        self.assertIn("aggregated_data", result)

if __name__ == "__main__":
    unittest.main()