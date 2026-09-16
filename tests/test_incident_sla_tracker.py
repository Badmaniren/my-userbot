import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import random
import io

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla,
    incident_notification_bridge,
    incident_auto_escalation_engine
)

class TestIncidentSLATrackerIntegration(unittest.TestCase):

    def setUp(self):
        self.severity_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
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

    def test_register_and_get_time_to_breach(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))

        self.tracker.register_incident(incident_id, severity, created_at)
        
        time_to_breach = self.tracker.get_time_to_breach(incident_id)
        expected_limit = self.sla_thresholds.get(severity, 3600)
        
        self.assertIsInstance(time_to_breach, float)
        self.assertLess(time_to_breach, expected_limit)

    def test_get_time_to_breach_not_found(self):
        fake_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(fake_id)

    def test_update_incident_status(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now()

        self.tracker.register_incident(incident_id, severity, created_at)
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(incident_id, new_status)

        self.assertEqual(self.tracker.incidents[incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breached(self):
        inc_warn_id = uuid.uuid4().hex
        inc_breach_id = uuid.uuid4().hex
        inc_active_id = uuid.uuid4().hex

        sev_warn = random.choice(self.severity_levels)
        sev_breach = random.choice(self.severity_levels)
        sev_active = random.choice(self.severity_levels)

        limit_warn = self.sla_thresholds[sev_warn]
        limit_breach = self.sla_thresholds[sev_breach]

        now = datetime.now()
        created_warn = now - timedelta(seconds=int(limit_warn * self.warning_threshold_pct) + 5)
        created_breach = now - timedelta(seconds=limit_breach + 100)
        created_active = now

        self.tracker.register_incident(inc_warn_id, sev_warn, created_warn)
        self.tracker.register_incident(inc_breach_id, sev_breach, created_breach)
        self.tracker.register_incident(inc_active_id, sev_active, created_active)

        mock_bridge = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )

        result_ids = [r["incident_id"] for r in results]
        self.assertIn(inc_warn_id, result_ids)
        self.assertIn(inc_breach_id, result_ids)
        self.assertNotIn(inc_active_id, result_ids)

        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=inc_breach_id, severity=sev_breach)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=inc_breach_id, severity=sev_breach)

    def test_track_incident_sla_function_with_timestamp(self):
        incident_id = uuid.uuid4().hex
        timestamp = int(datetime.now().timestamp()) - random.randint(500, 1000)
        threshold = random.randint(100, 2000)

        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            },
            "threshold_seconds": threshold
        }

        res = track_incident_sla(sla_input)

        self.assertEqual(res["incident_id"], incident_id)
        self.assertIn("breach_predicted", res)
        self.assertIn("time_remaining_seconds", res)
        self.assertIsInstance(res["breach_predicted"], bool)

    def test_track_incident_sla_function_without_timestamp(self):
        incident_id = uuid.uuid4().hex
        threshold = random.randint(100, 2000)

        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": {
                "data": {}
            },
            "threshold_seconds": threshold
        }

        res = track_incident_sla(sla_input)

        self.assertEqual(res["incident_id"], incident_id)
        self.assertFalse(res["breach_predicted"])

    def test_end_to_end_incident_sla_workflow(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now() - timedelta(seconds=random.randint(5, 50))

        self.tracker.register_incident(incident_id, severity, created_at)
        
        with patch("skills.incident_aggregator.aggregate_incidents") as mock_aggregate:
            mock_aggregate.return_value = {
                "status": uuid.uuid4().hex,
                "metrics": {uuid.uuid4().hex: random.randint(1, 100)}
            }
            
            aggregated_input = {
                "incident_id": incident_id,
                "aggregated_data": {
                    "data": {
                        "timestamp": int(created_at.timestamp())
                    }
                },
                "threshold_seconds": self.sla_thresholds[severity]
            }

            workflow_result = track_incident_sla(aggregated_input)
            self.assertEqual(workflow_result["incident_id"], incident_id)
            
            time_left = self.tracker.get_time_to_breach(incident_id)
            self.assertIsInstance(time_left, float)
            
            self.tracker.update_incident_status(incident_id, f"RESOLVED_{uuid.uuid4().hex[:4]}")
            breaches = self.tracker.check_sla_breaches()
            self.assertEqual(len(breaches), 0)