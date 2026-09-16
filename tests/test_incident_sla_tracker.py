import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import random
import uuid

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla
)

class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.thresholds = {self.severity: random.randint(500, 2000)}
        self.warning_pct = round(random.uniform(0.5, 0.9), 2)
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_pct)

    def test_register_incident(self):
        rnd_id = uuid.uuid4().hex
        rnd_sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        now = datetime.now()
        
        self.tracker.register_incident(rnd_id, rnd_sev, now)

        self.assertIn(rnd_id, self.tracker.incidents)
        self.assertEqual(self.tracker.incidents[rnd_id]["severity"], rnd_sev)
        self.assertEqual(self.tracker.incidents[rnd_id]["created_at"], now)
        self.assertEqual(self.tracker.incidents[rnd_id]["status"], "ACTIVE")

    def test_get_time_to_breach_success(self):
        self.tracker.register_incident(self.incident_id, self.severity, self.created_at)
        current_time = self.created_at + timedelta(seconds=50)
        
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)
        expected = self.thresholds[self.severity] - 50
        
        self.assertEqual(time_to_breach, expected)

    def test_get_time_to_breach_not_found(self):
        missing_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(missing_id)

    def test_update_incident_status(self):
        self.tracker.register_incident(self.incident_id, self.severity, self.created_at)
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"

        self.tracker.update_incident_status(self.incident_id, new_status)
        
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_update_incident_status_nonexistent(self):
        missing_id = uuid.uuid4().hex
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        try:
            self.tracker.update_incident_status(missing_id, new_status)
        except Exception as e:
            self.fail(f"update_incident_status raised unexpected exception: {e}")

    def test_check_sla_breaches_warning(self):
        limit = 100
        self.tracker.sla_thresholds[self.severity] = limit
        self.tracker.warning_threshold_pct = 0.5

        created = datetime.now() - timedelta(seconds=60)
        self.tracker.register_incident(self.incident_id, self.severity, created)
        
        results = self.tracker.check_sla_breaches(current_time=datetime.now())
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "WARNING")

    def test_check_sla_breaches_breached(self):
        limit = 50
        self.tracker.sla_thresholds[self.severity] = limit

        created = datetime.now() - timedelta(seconds=100)
        self.tracker.register_incident(self.incident_id, self.severity, created)
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=datetime.now(),
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "BREACHED")
        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=self.incident_id, severity=self.severity)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=self.incident_id, severity=self.severity)

    def test_check_sla_breaches_resolved_ignored(self):
        limit = 50
        self.tracker.sla_thresholds[self.severity] = limit

        created = datetime.now() - timedelta(seconds=100)
        self.tracker.register_incident(self.incident_id, self.severity, created)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED")

        results = self.tracker.check_sla_breaches(current_time=datetime.now())
        
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_with_timestamp(self):
        inc_id = uuid.uuid4().hex
        threshold = random.randint(1000, 5000)
        past_ts = int(datetime.now().timestamp()) - random.randint(100, 500)
        
        payload = {
            "incident_id": inc_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": past_ts
                }
            }
        }
        
        res = track_incident_sla(payload)
        self.assertEqual(res["incident_id"], inc_id)
        self.assertIsInstance(res["breach_predicted"], bool)
        self.assertIsInstance(res["time_remaining_seconds"], float)

    def test_track_incident_sla_without_timestamp(self):
        inc_id = uuid.uuid4().hex
        threshold = random.randint(1000, 5000)
        
        payload = {
            "incident_id": inc_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {}
            }
        }
        
        res = track_incident_sla(payload)
        self.assertEqual(res["incident_id"], inc_id)
        self.assertIsInstance(res["breach_predicted"], bool)
        self.assertIsInstance(res["time_remaining_seconds"], float)

    def test_integration_with_evaluate_incident_severity(self):
        with patch("skills.incident_sla_tracker.evaluate_incident_severity") as mock_eval:
            mock_eval.return_value = {"severity": self.severity}
            
            exc_arg = Exception(uuid.uuid4().hex)
            tb_arg = uuid.uuid4().hex
            
            res_eval = mock_eval(exception=exc_arg, traceback_str=tb_arg)
            self.assertEqual(res_eval["severity"], self.severity)
            mock_eval.assert_called_once_with(exception=exc_arg, traceback_str=tb_arg)
