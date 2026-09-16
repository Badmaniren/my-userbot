import unittest
import uuid
import random
import string
from skills.incident_post_mortem_service import IncidentPostMortemService

class TestIncidentPostMortemServiceIntegration(unittest.TestCase):
    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_generate_report_from_dict_integration(self):
        random_incident_id = str(uuid.uuid4())
        random_error_code = f"ERR_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
        random_timeout = random.randint(50, 500)
        random_memory_mb = random.randint(128, 2048)
        
        random_log_line_1 = f"DEBUG: Action initiated - {''.join(random.choices(string.ascii_lowercase, k=8))}"
        random_log_line_2 = f"ERROR: Connection failed - {''.join(random.choices(string.ascii_lowercase, k=8))}"
        raw_logs = f"{random_log_line_1}\n{random_log_line_2}".encode("utf-8")

        incident_data = {
            "incident_id": random_incident_id,
            "error_code": random_error_code,
            "metrics": {
                "timeout_count": random_timeout,
                "memory_leak_mb": random_memory_mb,
                "memory_leak_detected": True
            }
        }
        recovery_data = {
            "logs": raw_logs
        }

        report = self.service.generate_report(incident_data, recovery_data)

        self.assertIsNotNone(report)
        self.assertIn("report_id", report)
        self.assertEqual(report["incident_id"], random_incident_id)
        self.assertIsInstance(report["timeline"], list)
        
        root_cause = report["root_cause_analysis"]
        self.assertIn(random_error_code, root_cause)
        self.assertIn("Memory leak detected", root_cause)
        self.assertIn(f"High timeout count: {random_timeout}", root_cause)
        self.assertIn(random_log_line_1, root_cause)
        self.assertIn(random_log_line_2, root_cause)

        self.assertIn(random_log_line_1, report["recovery_logs_summary"])
        self.assertIn(random_log_line_2, report["recovery_logs_summary"])
        self.assertEqual(report["metrics_snapshot"]["timeout_count"], random_timeout)

    def test_generate_report_from_id_integration(self):
        random_incident_id = str(uuid.uuid4())

        report = self.service.generate_report(random_incident_id)

        self.assertIsNotNone(report)
        self.assertEqual(report["incident_id"], random_incident_id)
        self.assertIn("root_cause", report)
        self.assertIn("metrics_snapshot", report)
        self.assertIn("recovery_logs_summary", report)
        self.assertIsInstance(report["metrics_snapshot"], dict)
        self.assertIsInstance(report["recovery_logs_summary"], str)

if __name__ == "__main__":
    unittest.main()