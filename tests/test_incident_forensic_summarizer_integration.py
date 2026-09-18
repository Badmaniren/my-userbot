import unittest
import os
import uuid
import random
from io import BytesIO
from skills.incident_forensic_summarizer import start_new, incident_forensic_summarizer

class TestIncidentForensicSummarizerIntegration(unittest.TestCase):

    def setUp(self):
        self.created_files = []

    def tearDown(self):
        for file_path in self.created_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_start_new_integration_flow(self):
        random_suffix = uuid.uuid4().hex[:8]
        test_incident_id = f"INC-TEST-{random_suffix}"

        telemetry_content = f"cpu_load={random.randint(90, 100)}% memory_leak=true id={random_suffix}"
        telemetry_stream = BytesIO(telemetry_content.encode('utf-8'))

        result = start_new(
            incident_id=test_incident_id,
            telemetry_source=telemetry_stream
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_incident_id"), test_incident_id)
        self.assertIn("summary_id", result)

        report_path = result.get("report_file_path")
        self.assertIsNotNone(report_path)
        self.created_files.append(report_path)

        self.assertTrue(os.path.exists(report_path), f"Report file {report_path} was not created on disk")

        with open(report_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(test_incident_id, file_content)
            self.assertIn(telemetry_content, file_content)

    def test_incident_forensic_summarizer_direct_call(self):
        random_suffix = uuid.uuid4().hex[:8]
        custom_incident_id = f"CUSTOM-{random_suffix}"
        random_payload_key = f"metric_{random.randint(1000, 9999)}"
        random_payload_val = f"val_{random.randint(1000, 9999)}"

        incident_data = {
            "incident_id": custom_incident_id,
            "telemetry_payload": {random_payload_key: random_payload_val}
        }

        result = incident_forensic_summarizer(
            incident_data=incident_data,
            include_telemetry_dump=True
        )

        self.assertEqual(result.get("target_incident_id"), custom_incident_id)
        self.assertIn(random_payload_key, result.get("telemetry_dump", ""))
        self.assertIn(random_payload_val, result.get("telemetry_dump", ""))

        report_path = result.get("report_file_path")
        self.created_files.append(report_path)
        self.assertTrue(os.path.exists(report_path))

if __name__ == "__main__":
    unittest.main()