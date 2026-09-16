import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os
import glob

from skills.incident_sla_violation_analyzer import IncidentSLAViolationAnalyzer

class TestIncidentSLAViolationAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = IncidentSLAViolationAnalyzer()
        self.random_cause = ''.join(random.choices(string.ascii_lowercase, k=12))
        self.random_score = round(random.uniform(0.1, 0.99), 2)
        self.incident_payload = {
            "id": uuid.uuid4().hex,
            "cause": self.random_cause
        }
        self.prediction_payload = {
            "metric_id": uuid.uuid4().hex,
            "score": self.random_score
        }

    def test_analyze_root_causes_success(self):
        result = self.analyzer.analyze_root_causes(self.incident_payload, self.prediction_payload)

        self.assertIn("analysis_id", result)
        self.assertEqual(result["root_cause"], self.random_cause)
        self.assertEqual(result["prediction_score"], self.random_score)
        self.assertIsInstance(result["actionable_insights"], list)
        self.assertTrue(len(result["actionable_insights"]) > 0)

    def test_analyze_root_causes_empty_data(self):
        with self.assertRaises(ValueError):
            self.analyzer.analyze_root_causes({})

    def test_analyze_root_causes_with_mocked_dependency(self):
        mock_aggregator = MagicMock()
        mock_aggregator.fetch_telemetry.return_value = io.BytesIO(uuid.uuid4().bytes)

        with patch('uuid.uuid4') as mock_uuid:
            expected_uuid = uuid.UUID('12345678123456781234567812345678')
            mock_uuid.return_value = expected_uuid

            result = self.analyzer.analyze_root_causes(self.incident_payload, self.prediction_payload)

            self.assertEqual(result["analysis_id"], expected_uuid.hex)
            self.assertEqual(result["root_cause"], self.random_cause)

    def tearDown(self):
        for f in glob.glob("sla_analysis_*.json"):
            try:
                os.remove(f)
            except OSError:
                pass

if __name__ == '__main__':
    unittest.main()