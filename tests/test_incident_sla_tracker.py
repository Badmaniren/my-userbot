import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import random
import uuid

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla,
)


class TestIncidentSLATrackerUnit(unittest.TestCase):
    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.thresholds = {
            "LOW": random.randint(7000, 10000),
            "MEDIUM": random.randint(4000, 6000),
            "HIGH": random.randint(1800, 3600),
            "CRITICAL": random.randint(600, 1200),
        }
        self.warning_pct = round(random.uniform(0.5, 0.8), 2)
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.thresholds,
            warning_threshold_pct=self.warning_pct
        )

    def test_register_incident(self):
        now = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, now)
        self.assertIn(self.incident_id, self.tracker.incidents)
        self.assertEqual(self.tracker.incidents[self.incident_id]["severity"], self.severity)
        self.assertEqual(self.tracker.incidents[self.incident_id]["created_at"], now)
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], "ACTIVE")

    def test_get_time_to_breach_success(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(100, 500))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time=current_time)

        sla_limit = self.thresholds.get(self.severity, 3600)
        elapsed = (current_time - created_at).total_seconds()
        expected_remaining = float(sla_limit - elapsed)
        
        self.assertEqual(time_to_breach, expected_remaining)

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

    def test_check_sla_breaches_warning(self):
        sla_limit = self.thresholds.get(self.severity, 3600)
        offset_seconds = int(sla_limit * self.warning_pct) + random.randint(1, 10)
        created_at = datetime.now() - timedelta(seconds=offset_seconds)

        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        results = self.tracker.check_sla_breaches(current_time=datetime.now())

        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "WARNING" for r in results))

    def test_check_sla_breaches_breached(self):
        sla_limit = self.thresholds.get(self.severity, 3600)
        offset_seconds = sla_limit + random.randint(10, 100)
        created_at = datetime.now() - timedelta(seconds=offset_seconds)
        
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=datetime.now(),
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        mock_bridge.notify_sla_breach.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )
        mock_escalation.escalate_incident.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )
        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "BREACHED" for r in results))

    def test_check_sla_breaches_resolved_skipped(self):
        sla_limit = self.thresholds.get(self.severity, 3600)
        offset_seconds = sla_limit + random.randint(100, 200)
        created_at = datetime.now() - timedelta(seconds=offset_seconds)
        
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED")
        
        results = self.tracker.check_sla_breaches(current_time=datetime.now())
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(50, 500)
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
        
        res = track_incident_sla(sla_input)
        self.assertEqual(res["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", res)
        self.assertIn("time_remaining_seconds", res)
        self.assertIsInstance(res["time_remaining_seconds"], float)


class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_tracking_pipeline(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(["CRITICAL", "HIGH"])
        thresholds = {severity: random.randint(100, 500)}
        
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=0.5)
        created_at = datetime.now() - timedelta(seconds=random.randint(600, 1000))
        
        tracker.register_incident(incident_id, severity, created_at)
        
        with patch("skills.incident_severity_evaluator.evaluate_incident_severity") as mock_eval:
            mock_eval.return_value = {"severity": severity}

            with patch("skills.incident_aggregator.aggregate_incidents") as mock_agg:
                mock_agg.return_value = {"aggregated": True, "incidents_count": 1}

                eval_result = mock_eval(uuid.uuid4().hex)
                self.assertEqual(eval_result["severity"], severity)

                raw_event = {
                    "id": uuid.uuid4().hex,
                    "timestamp": datetime.now().timestamp()
                }

                agg_result = mock_agg(
                    [raw_event],
                    exception=Exception(uuid.uuid4().hex),
                    traceback_str=uuid.uuid4().hex
                )
                self.assertTrue(agg_result["aggregated"])

                breaches = tracker.check_sla_breaches(current_time=datetime.now())
                self.assertTrue(any(b["incident_id"] == incident_id and b["status"] == "BREACHED" for b in breaches))