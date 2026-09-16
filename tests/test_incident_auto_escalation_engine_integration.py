import unittest
import uuid
import random
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine, escalate_incident_automatically

class TestIncidentAutoEscalationEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()
        self.test_incident_id = str(uuid.uuid4())
        self.test_error_message = f"Critical system failure code: {random.randint(1000, 9999)}"
        self.test_severity = random.choice(["CRITICAL", "FATAL", "EMERGENCY"])

    def test_escalate_critical_incident_real_flow(self):
        result = self.engine.escalate_critical_incident(
            self.test_incident_id,
            self.test_error_message,
            self.test_severity
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.test_incident_id)
        self.assertEqual(result.get("status"), "escalated")
        self.assertIn("aggregator_result", result)
        self.assertIn("pipeline_result", result)

    def test_escalate_incident_automatically_real_flow(self):
        random_error_code = f"ERR-{random.randint(100, 999)}"
        random_payload = f"Payload data stream {uuid.uuid4()}"

        aggregated_input = {
            "incident_id": self.test_incident_id,
            "error_code": random_error_code,
            "payload": random_payload
        }

        result = escalate_incident_automatically(aggregated_input)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "escalated")
        self.assertEqual(result.get("incident_id"), self.test_incident_id)
        self.assertEqual(result.get("error_code"), random_error_code)
        self.assertEqual(result.get("payload"), random_payload)

if __name__ == "__main__":
    unittest.main()