import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string

from skills.incident_sla_breach_predictor import (
    IncidentSLABreachPredictor,
    incident_sla_breach_predictor
)


class TestIncidentSLABreachPredictor(unittest.TestCase):

    def setUp(self):
        self.predictor = IncidentSLABreachPredictor()
        self.incident_id = str(uuid.uuid4())
        self.trend_id = str(uuid.uuid4())

    def test_forecast_breach_success_with_time_remaining(self):
        limit_seconds = random.randint(600, 3600)
        elapsed_seconds = random.randint(100, 500)
        risk = round(random.uniform(0.0, 0.4), 2)
        priority = random.choice(["LOW", "MEDIUM"])

        mock_sla_data = {
            "sla_limit_seconds": limit_seconds,
            "current_elapsed_seconds": elapsed_seconds,
            "priority": priority,
            "status": "ACTIVE"
        }
        mock_trend_data = {
            "risk_score": risk,
            "trend_id": self.trend_id
        }

        with patch("skills.incident_sla_breach_predictor.incident_sla_tracker") as mock_tracker, \
             patch("skills.incident_sla_breach_predictor.incident_trend_analyzer") as mock_analyzer:

            mock_tracker.get_tracking_data.return_value = mock_sla_data
            mock_analyzer.analyze.return_value = mock_trend_data

            result = self.predictor.forecast_breach(self.incident_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["trend_reference"], self.trend_id)
            self.assertFalse(result["breach_predicted"])

    def test_forecast_breach_triggered_by_status(self):
        mock_sla_data = {
            "status": "BREACHED",
            "priority": "LOW"
        }
        mock_trend_data = {
            "risk_score": 0.0,
            "trend_id": self.trend_id
        }

        with patch("skills.incident_sla_breach_predictor.incident_sla_tracker") as mock_tracker, \
             patch("skills.incident_sla_breach_predictor.incident_trend_analyzer") as mock_analyzer:

            mock_tracker.get_tracking_data.return_value = mock_sla_data
            mock_analyzer.analyze.return_value = mock_trend_data

            result = self.predictor.forecast_breach(self.incident_id)

            self.assertTrue(result["breach_predicted"])
            self.assertEqual(result["incident_id"], self.incident_id)

    def test_forecast_breach_triggered_by_risk_score(self):
        risk = round(random.uniform(0.6, 0.99), 2)
        mock_sla_data = {
            "status": "ACTIVE",
            "priority": "LOW",
            "time_remaining_minutes": random.randint(500, 1000)
        }
        mock_trend_data = {
            "risk_factor": risk,
            "trend_id": self.trend_id
        }

        with patch("skills.incident_sla_breach_predictor.incident_sla_tracker") as mock_tracker, \
             patch("skills.incident_sla_breach_predictor.incident_trend_analyzer") as mock_analyzer:

            mock_tracker.get_tracking_data.return_value = mock_sla_data
            mock_analyzer.analyze.return_value = mock_trend_data

            result = self.predictor.forecast_breach(self.incident_id)

            self.assertTrue(result["breach_predicted"])

    def test_forecast_breach_triggered_by_critical_priority_and_time(self):
        priority = random.choice(["HIGH", "CRITICAL"])
        time_rem = random.randint(10, 150)
        mock_sla_data = {
            "status": "ACTIVE",
            "priority": priority,
            "time_remaining_minutes": time_rem
        }
        mock_trend_data = {
            "risk_score": 0.1,
            "trend_id": self.trend_id
        }

        with patch("skills.incident_sla_breach_predictor.incident_sla_tracker") as mock_tracker, \
             patch("skills.incident_sla_breach_predictor.incident_trend_analyzer") as mock_analyzer:

            mock_tracker.get_tracking_data.return_value = mock_sla_data
            mock_analyzer.analyze.return_value = mock_trend_data

            result = self.predictor.forecast_breach(self.incident_id)

            self.assertTrue(result["breach_predicted"])

    def test_forecast_breach_raises_value_error_when_no_data(self):
        with patch("skills.incident_sla_breach_predictor.incident_sla_tracker") as mock_tracker:
            mock_tracker.get_tracking_data.return_value = None
            mock_tracker.side_effect = None
            
            # Making sure all fallbacks fail to return data
            with patch("skills.incident_sla_breach_predictor.callable", return_value=False):
                with self.assertRaises(ValueError):
                    self.predictor.forecast_breach(self.incident_id)

    def test_consume_forecaster_stream(self):
        expected_stream_data = "".join(random.choices(string.ascii_letters, k=25))
        with patch("skills.incident_sla_breach_predictor.incident_trend_forecaster") as mock_forecaster:
            mock_forecaster.stream_forecast.return_value = expected_stream_data
            res = self.predictor.consume_forecaster_stream()
            self.assertEqual(res, expected_stream_data)

    def test_force_escalate_prediction(self):
        expected_escalation_status = random.choice([True, False])
        with patch("skills.incident_sla_breach_predictor.incident_auto_escalation_engine") as mock_engine:
            mock_engine.trigger_escalation.return_value = expected_escalation_status
            res = self.predictor.force_escalate_prediction(self.incident_id)
            self.assertEqual(res, expected_escalation_status)
            mock_engine.trigger_escalation.assert_called_once_with(self.incident_id)

    def test_functional_incident_sla_breach_predictor_positive(self):
        limit = random.randint(100, 200)
        elapsed = random.randint(180, 250)
        payload = {
            "incident_id": self.incident_id,
            "sla_data": {
                "sla_limit_seconds": limit,
                "current_elapsed_seconds": elapsed,
                "status": "ACTIVE"
            },
            "trend_data": {
                "risk_score": 0.2,
                "trend_id": self.trend_id
            }
        }
        result = incident_sla_breach_predictor(payload)
        self.assertTrue(result["breach_predicted"])
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertEqual(result["trend_reference"], self.trend_id)

    def test_functional_incident_sla_breach_predictor_negative(self):
        limit = random.randint(1000, 2000)
        elapsed = random.randint(10, 100)
        payload = {
            "incident_id": self.incident_id,
            "sla_data": {
                "sla_limit_seconds": limit,
                "current_elapsed_seconds": elapsed,
                "status": "OK"
            },
            "trend_data": {
                "risk_factor": 0.1,
                "trend_id": self.trend_id
            }
        }
        result = incident_sla_breach_predictor(payload)
        self.assertFalse(result["breach_predicted"])
        self.assertEqual(result["incident_id"], self.incident_id)


if __name__ == "__main__":
    unittest.main()