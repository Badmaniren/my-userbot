import unittest
from unittest.mock import patch
import uuid
import random
from skills.incident_sla_breach_predictor import IncidentSLABreachPredictor, incident_sla_breach_predictor

class TestIncidentSLABreachPredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = IncidentSLABreachPredictor()
        self.incident_id = uuid.uuid4().hex
        self.trend_id = uuid.uuid4().hex

    def test_forecast_breach_with_object_trackers(self):
        mock_sla_tracker = unittest.mock.MagicMock()
        mock_sla_tracker.get_tracking_data.return_value = {
            "sla_limit_seconds": random.randint(100, 500),
            "current_elapsed_seconds": random.randint(0, 50),
            "priority": random.choice(["LOW", "MEDIUM"])
        }

        mock_trend_analyzer = unittest.mock.MagicMock()
        mock_trend_analyzer.analyze.return_value = {
            "risk_score": random.uniform(0.0, 0.4),
            "trend_id": self.trend_id
        }

        with patch("skills.incident_sla_breach_predictor.incident_sla_tracker", mock_sla_tracker), \
             patch("skills.incident_sla_breach_predictor.incident_trend_analyzer", mock_trend_analyzer):
            
            result = self.predictor.forecast_breach(self.incident_id)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["trend_reference"], self.trend_id)
            self.assertIn("breach_predicted", result)

    def test_forecast_breach_missing_data_raises(self):
        mock_sla_tracker = unittest.mock.MagicMock()
        mock_sla_tracker.get_tracking_data.return_value = None

        with patch("skills.incident_sla_breach_predictor.incident_sla_tracker", mock_sla_tracker):
            with self.assertRaises(ValueError):
                self.predictor.forecast_breach(self.incident_id)

    def test_consume_forecaster_stream(self):
        expected_stream = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_forecaster = unittest.mock.MagicMock()
        mock_forecaster.stream_forecast.return_value = expected_stream

        with patch("skills.incident_sla_breach_predictor.incident_trend_forecaster", mock_forecaster):
            res = self.predictor.consume_forecaster_stream()
            self.assertEqual(res, expected_stream)

    def test_force_escalate_prediction(self):
        mock_escalation = unittest.mock.MagicMock()
        mock_escalation.trigger_escalation.return_value = True

        with patch("skills.incident_sla_breach_predictor.incident_auto_escalation_engine", mock_escalation):
            res = self.predictor.force_escalate_prediction(self.incident_id)
            self.assertTrue(res)
            mock_escalation.trigger_escalation.assert_called_once_with(self.incident_id)

    def test_functional_incident_sla_breach_predictor(self):
        payload = {
            "incident_id": self.incident_id,
            "sla_data": {
                "sla_limit_seconds": random.randint(10, 50),
                "current_elapsed_seconds": random.randint(100, 200)
            },
            "trend_data": {
                "risk_factor": random.uniform(1.1, 2.0),
                "trend_id": self.trend_id
            }
        }
        res = incident_sla_breach_predictor(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["incident_id"], self.incident_id)
        self.assertTrue(res["breach_predicted"])
        self.assertEqual(res["trend_reference"], self.trend_id)

if __name__ == "__main__":
    unittest.main()