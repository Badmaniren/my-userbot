import unittest
import os
import uuid
import json
import time
from skills.incident_aggregator import store_incident_metrics
from skills.incident_recovery_duration_tracker import track_recovery_duration

class TestIncidentRecoveryDurationTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.start_time = int(time.time())
        self.end_time = self.start_time + 3600
        self.report_filename = f"recovery_log_{self.incident_id}.json"

        self.test_data = {
            "incident_id": self.incident_id,
            "start_timestamp": self.start_time,
            "end_timestamp": self.end_time,
            "status": "resolved"
        }
        store_incident_metrics(self.test_data)

    def tearDown(self):
        if os.path.exists(self.report_filename):
            os.remove(self.report_filename)

    def test_track_recovery_duration_integration(self):
        result = track_recovery_duration(self.incident_id)

        self.assertIsNotNone(result)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertEqual(result["duration_seconds"], 3600)

        self.assertTrue(os.path.exists(self.report_filename), "Report file was not created")

        with open(self.report_filename, 'r') as f:
            file_content = json.load(f)
            self.assertEqual(file_content["incident_id"], self.incident_id)
            self.assertEqual(file_content["recovery_duration"], 3600)

    def test_track_recovery_duration_nonexistent_incident(self):
        fake_id = str(uuid.uuid4())
        result = track_recovery_duration(fake_id)
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(f"recovery_log_{fake_id}.json"))

if __name__ == '__main__':
    unittest.main()
