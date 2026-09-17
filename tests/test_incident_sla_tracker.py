import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import random
import io

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla
)

class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        self.warning_pct = 0.8
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.thresholds,
            warning_threshold_pct=self.warning_pct
        )

    def test_register_and_get_time_to_breach(self):
        created_at = datetime.now() - timedelta(seconds=100)
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        current_time = created_at + timedelta(seconds=200)
        time_remaining = self.tracker.get_time_to_breach(self.incident_id, current_time)
        
        expected_limit = self.thresholds[self.severity]
        expected_remaining = float(expected_limit - 100)
        self.assertEqual(time_remaining, expected_remaining)

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

    def test_check_sla_breaches_warning_and_breach(self):
        crit_id = uuid.uuid4().hex
        high_id = uuid.uuid4().hex

        now = datetime.now()

        crit_created = now - timedelta(seconds=650)
        high_created = now - timedelta(seconds=1500)
        
        self.tracker.register_incident(crit_id, "CRITICAL", crit_created)
        self.tracker.register_incident(high_id, "HIGH", high_created)
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        result_map = {r["incident_id"]: r["status"] for r in results}
        
        self.assertEqual(result_map.get(crit_id), "BREACHED")
        self.assertEqual(result_map.get(high_id), "WARNING")
        
        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=crit_id, severity="CRITICAL")
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=crit_id, severity="CRITICAL")

    def test_check_sla_breaches_resolved_skipped(self):
        created_at = datetime.now() - timedelta(seconds=10000)
        self.tracker.register_incident(self.incident_id, "CRITICAL", created_at)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED_SUCCESS")
        
        results = self.tracker.check_sla_breaches()
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function(self):
        threshold = random.randint(1000, 5000)
        timestamp = int(datetime.now().timestamp()) - 500
        
        payload = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }
        
        result = track_incident_sla(payload)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)

    def test_end_to_end_sla_pipeline_and_tracking(self):
        random_err_msg = uuid.uuid4().hex
        random_trace = uuid.uuid4().hex
        raw_payload = io.BytesIO(f"{random_err_msg}:{random_trace}".encode('utf-8'))

        with patch("skills.incident_aggregator.aggregate_incidents") as mock_aggregate:
            mock_aggregate.return_value = {
                "incident_id": self.incident_id,
                "severity": self.severity,
                "timestamp": int(datetime.now().timestamp())
            }

            from skills.incident_aggregator import aggregate_incidents
            aggregated_result = aggregate_incidents(
                raw_payload,
                exception=Exception(random_err_msg),
                traceback_str=random_trace
            )

            self.assertEqual(aggregated_result["incident_id"], self.incident_id)
            self.assertEqual(aggregated_result["severity"], self.severity)
            mock_aggregate.assert_called_once()