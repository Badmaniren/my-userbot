import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.incident_financial_impact_evaluator import IncidentFinancialImpactEvaluator

class TestIncidentFinancialImpactEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = IncidentFinancialImpactEvaluator()

    def test_evaluate_financial_impact_success(self):
        incident_id = str(uuid.uuid4())
        base_loss = round(random.uniform(1000.0, 50000.0), 2)
        downtime_hours = random.randint(1, 72)
        hourly_rate = round(random.uniform(100.0, 5000.0), 2)
        
        mock_impact_data = {
            "incident_id": incident_id,
            "downtime_hours": downtime_hours,
            "affected_users": random.randint(10, 10000),
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        }

        with patch("skills.incident_impact_analyzer.IncidentImpactAnalyzer.get_impact_data") as mock_get_impact:
            mock_get_impact.return_value = mock_impact_data

            with patch.dict("os.environ", {"BASE_HOURLY_RATE_LOSS": str(hourly_rate)}):
                result = self.evaluator.evaluate(incident_id)

                self.assertIsInstance(result, dict)
                self.assertEqual(result["incident_id"], incident_id)
                self.assertIn("total_financial_loss", result)
                self.assertGreaterEqual(result["total_financial_loss"], 0.0)
                mock_get_impact.assert_called_once_with(incident_id)

    def test_evaluate_financial_impact_analyzer_error(self):
        incident_id = str(uuid.uuid4())
        error_message = f"error_msg_{uuid.uuid4().hex}"

        with patch("skills.incident_impact_analyzer.IncidentImpactAnalyzer.get_impact_data") as mock_get_impact:
            mock_get_impact.side_effect = Exception(error_message)

            with self.assertRaises(ValueError) as context:
                self.evaluator.evaluate(incident_id)

            self.assertIn(error_message, str(context.exception))
            mock_get_impact.assert_called_once_with(incident_id)

    def test_evaluate_financial_impact_missing_data(self):
        incident_id = str(uuid.uuid4())
        
        with patch("skills.incident_impact_analyzer.IncidentImpactAnalyzer.get_impact_data") as mock_get_impact:
            mock_get_impact.return_value = None

            with self.assertRaises(ValueError):
                self.evaluator.evaluate(incident_id)

            mock_get_impact.assert_called_once_with(incident_id)

    def test_evaluate_financial_impact_with_io_stream(self):
        incident_id = str(uuid.uuid4())
        random_bytes = uuid.uuid4().bytes
        stream_mock = io.BytesIO(random_bytes)

        with patch("skills.incident_impact_analyzer.IncidentImpactAnalyzer.get_impact_data") as mock_get_impact:
            mock_get_impact.return_value = {
                "incident_id": incident_id,
                "downtime_hours": 5,
                "stream_data": stream_mock
            }

            result = self.evaluator.evaluate(incident_id)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["incident_id"], incident_id)

if __name__ == "__main__":
    unittest.main()