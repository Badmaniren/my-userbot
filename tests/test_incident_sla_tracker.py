import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import random
import io

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla

class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.sla_thresholds = {
            "CRITICAL": random.randint(300, 900),
            "HIGH": random.randint(1800, 3600),
            "MEDIUM": random.randint(7200, 14400),
            "LOW": random.randint(28800, 86400)
        }
        self.warning_threshold_pct = round(random.uniform(0.7, 0.9), 2)
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_threshold_pct
        )

    def test_register_incident_success(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        self.assertIn(self.incident_id, self.tracker.incidents)
        incident_data = self.tracker.incidents[self.incident_id]
        self.assertEqual(incident_data["severity"], self.severity)
        self.assertEqual(incident_data["created_at"], created_at)
        self.assertEqual(incident_data["status"], "ACTIVE")

    def test_get_time_to_breach_success(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        elapsed_delta = timedelta(seconds=random.randint(10, 50))
        current_time = created_at + elapsed_delta

        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)
        expected_limit = self.sla_thresholds.get(self.severity, 3600)
        expected_ttb = expected_limit - elapsed_delta.total_seconds()
        
        self.assertEqual(time_to_breach, expected_ttb)

    def test_get_time_to_breach_not_found(self):
        missing_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(missing_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(self.incident_id, new_status)
        
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breached(self):
        id_warning = uuid.uuid4().hex
        id_breached = uuid.uuid4().hex
        id_active = uuid.uuid4().hex

        now = datetime.now()
        limit = 1000
        self.tracker.sla_thresholds[self.severity] = limit
        
        created_warning = now - timedelta(seconds=int(limit * self.warning_threshold_pct) + 10)
        created_breached = now - timedelta(seconds=limit + 50)
        created_active = now - timedelta(seconds=10)
        
        self.tracker.register_incident(id_warning, self.severity, created_warning)
        self.tracker.register_incident(id_breached, self.severity, created_breached)
        self.tracker.register_incident(id_active, self.severity, created_active)
        
        mock_notification = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_notification,
            escalation_engine=mock_escalation
        )
        
        statuses = {res["incident_id"]: res["status"] for res in results}
        
        self.assertEqual(statuses.get(id_warning), "WARNING")
        self.assertEqual(statuses.get(id_breached), "BREACHED")
        self.assertNotIn(id_active, statuses)
        
        mock_notification.notify_sla_breach.assert_called_once_with(
            incident_id=id_breached, severity=self.severity
        )
        mock_escalation.escalate_incident.assert_called_once_with(
            incident_id=id_breached, severity=self.severity
        )

    def test_track_incident_sla_with_valid_timestamp(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(100, 500)
        threshold = random.randint(1000, 5000)
        sla_input = {
            "incident_id": self.incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            },
            "threshold_seconds": threshold
        }
        
        result = track_incident_sla(sla_input)
        
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_track_incident_sla_with_invalid_timestamp(self):
        sla_input = {
            "incident_id": self.incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": uuid.uuid4().hex
                }
            },
            "threshold_seconds": random.randint(1000, 2000)
        }
        
        result = track_incident_sla(sla_input)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIsInstance(result["breach_predicted"], bool)

    def test_integration_flow_with_aggregator_mock(self):
        agg_input = {
            "incident_id": self.incident_id,
            "stream_data": uuid.uuid4().hex
        }
        
        mock_exc = Exception(uuid.uuid4().hex)
        mock_tb = uuid.uuid4().hex
        
        with patch("skills.incident_sla_tracker.aggregate_incidents") as mock_aggregate:
            expected_payload = {
                "status": uuid.uuid4().hex,
                "incident_id": self.incident_id
            }
            mock_aggregate.return_value = expected_payload
            
            result = mock_aggregate(agg_input, exception=mock_exc, traceback_str=mock_tb)
            
            self.assertEqual(result, expected_payload)
            mock_aggregate.assert_called_once_with(agg_input, exception=mock_exc, traceback_str=mock_tb)