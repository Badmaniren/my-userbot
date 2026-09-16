import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.incident_sla_breach_predictor import IncidentSLABreachPredictor


class TestIncidentSLABreachPredictor(unittest.TestCase):

    def setUp(self):
        self.predictor = IncidentSLABreachPredictor()

    def test_predict_breach_success_flow(self):
        random_incident_id = f"inc_{uuid.uuid4().hex[:8]}"
        random_trend_id = f"trend_{uuid.uuid4().hex[:8]}"
        random_threshold = random.randint(10, 120)
        
        mock_trend_data = {
            "trend_id": random_trend_id,
            "velocity": random.uniform(1.1, 5.5),
            "risk_score": random.uniform(0.7, 0.99)
        }
        
        mock_sla_data = {
            "incident_id": random_incident_id,
            "time_remaining_minutes": random_threshold,
            "priority": random.choice(["HIGH", "CRITICAL", "MEDIUM"])
        }

        with patch("skills.incident_sla_breach_predictor.incident_trend_analyzer") as mock_trend, \
             patch("skills.incident_sla_breach_predictor.incident_sla_tracker") as mock_tracker:
            
            mock_trend.analyze.return_value = mock_trend_data
            mock_tracker.get_tracking_data.return_value = mock_sla_data

            result = self.predictor.forecast_breach(random_incident_id)

            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("breach_predicted"))
            self.assertEqual(result.get("incident_id"), random_incident_id)
            self.assertEqual(result.get("trend_reference"), random_trend_id)
            mock_trend.analyze.assert_called_once()
            mock_tracker.get_tracking_data.assert_called_with(random_incident_id)

    def test_predict_breach_no_risk(self):
        random_incident_id = f"inc_{uuid.uuid4().hex[:8]}"
        random_trend_id = f"trend_{uuid.uuid4().hex[:8]}"
        
        mock_trend_data = {
            "trend_id": random_trend_id,
            "velocity": 0.1,
            "risk_score": 0.05
        }
        
        mock_sla_data = {
            "incident_id": random_incident_id,
            "time_remaining_minutes": 1440,
            "priority": "LOW"
        }

        with patch("skills.incident_sla_breach_predictor.incident_trend_analyzer") as mock_trend, \
             patch("skills.incident_sla_breach_predictor.incident_sla_tracker") as mock_tracker:
            
            mock_trend.analyze.return_value = mock_trend_data
            mock_tracker.get_tracking_data.return_value = mock_sla_data

            result = self.predictor.forecast_breach(random_incident_id)

            self.assertFalse(result.get("breach_predicted"))
            self.assertEqual(result.get("incident_id"), random_incident_id)

    def test_forecast_with_stream_data(self):
        random_bytes_content = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes_content)

        with patch("skills.incident_sla_breach_predictor.incident_trend_forecaster") as mock_forecaster:
            mock_forecaster.stream_forecast.return_value = mock_stream

            stream_res = self.predictor.consume_forecaster_stream()
            
            self.assertIsInstance(stream_res, io.BytesIO)
            content = stream_res.read()
            self.assertEqual(content, random_bytes_content)
            mock_forecaster.stream_forecast.assert_called_once()

    def test_handle_missing_incident_data(self):
        random_incident_id = f"inc_missing_{uuid.uuid4().hex[:6]}"

        with patch("skills.incident_sla_breach_predictor.incident_sla_tracker") as mock_tracker:
            mock_tracker.get_tracking_data.return_value = None

            with self.assertRaises(ValueError) as ctx:
                self.predictor.forecast_breach(random_incident_id)
            
            self.assertIn(random_incident_id, str(ctx.exception))
            mock_tracker.get_tracking_data.assert_called_once_with(random_incident_id)

    def test_escalation_dispatch_trigger(self):
        random_incident_id = f"inc_esc_{uuid.uuid4().hex[:8]}"
        random_payload_key = uuid.uuid4().hex

        with patch("skills.incident_sla_breach_predictor.incident_auto_escalation_engine") as mock_escalation:
            mock_escalation.trigger_escalation.return_value = {
                "status": "DISPATCHED",
                "payload_ref": random_payload_key
            }

            res = self.predictor.force_escalate_prediction(random_incident_id)

            self.assertEqual(res.get("status"), "DISPATCHED")
            self.assertEqual(res.get("payload_ref"), random_payload_key)
            mock_escalation.trigger_escalation.assert_called_once_with(random_incident_id)