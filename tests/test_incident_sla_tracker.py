import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import random
import string

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.thresholds = {
            "LOW": random.randint(7200, 10800),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(300, 1799)
        }
        self.warning_pct = round(random.uniform(0.5, 0.9), 2)
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.thresholds,
            warning_threshold_pct=self.warning_pct
        )

    def test_register_incident_and_time_to_breach_success(self):
        created_at = datetime.now() - timedelta(seconds=100)
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.severity,
            created_at=created_at
        )

        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(
            incident_id=self.incident_id,
            current_time=current_time
        )

        expected_limit = self.thresholds.get(self.severity, 3600)
        expected_elapsed = (current_time - created_at).total_seconds()
        expected_remaining = expected_limit - expected_elapsed

        self.assertAlmostEqual(time_to_breach, expected_remaining, delta=1.0)

    def test_get_time_to_breach_raises_key_error(self):
        non_existent_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(incident_id=non_existent_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.severity,
            created_at=created_at
        )

        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(
            incident_id=self.incident_id,
            status=new_status
        )

        self.assertEqual(
            self.tracker.incidents[self.incident_id]["status"],
            new_status
        )

    def test_check_sla_breaches_active_and_warning(self):
        created_at = datetime.now() - timedelta(seconds=4000)
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity="MEDIUM",
            created_at=created_at
        )
        self.tracker.sla_thresholds["MEDIUM"] = 5000
        self.tracker.warning_threshold_pct = 0.5

        results = self.tracker.check_sla_breaches(current_time=datetime.now())
        
        found = False
        for res in results:
            if res["incident_id"] == self.incident_id:
                found = True
                self.assertEqual(res["status"], "WARNING")
        self.assertTrue(found)

    def test_check_sla_breaches_breached_triggers_hooks(self):
        created_at = datetime.now() - timedelta(seconds=6000)
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity="HIGH",
            created_at=created_at
        )
        self.tracker.sla_thresholds["HIGH"] = 3000

        mock_bridge = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=datetime.now(),
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )

        mock_bridge.notify_sla_breach.assert_called_once_with(
            incident_id=self.incident_id,
            severity="HIGH"
        )
        mock_escalation.escalate_incident.assert_called_once_with(
            incident_id=self.incident_id,
            severity="HIGH"
        )

        breached_found = any(r["incident_id"] == self.incident_id and r["status"] == "BREACHED" for r in results)
        self.assertTrue(breached_found)

    def test_check_sla_breaches_ignores_resolved(self):
        created_at = datetime.now() - timedelta(seconds=10000)
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity="LOW",
            created_at=created_at
        )
        self.tracker.update_incident_status(
            incident_id=self.incident_id,
            status="RESOLVED_SUCCESS"
        )

        results = self.tracker.check_sla_breaches()
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function_with_timestamp(self):
        timestamp = int(datetime.now().timestamp()) - 500
        threshold = random.randint(1000, 5000)
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }

        result = track_incident_sla(sla_input)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)

    def test_track_incident_sla_function_without_timestamp(self):
        threshold = random.randint(1000, 5000)
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {}
            }
        }

        result = track_incident_sla(sla_input)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)

    def test_integration_mock_aggregate_incidents(self):
        random_exception_str = "".join(random.choices(string.ascii_letters, k=10))
        random_traceback_str = "".join(random.choices(string.ascii_letters, k=20))
        random_raw_event = {"id": self.incident_id, "data": random.randint(1, 100)}

        with patch("skills.incident_sla_tracker.aggregate_incidents") as mock_aggregate:
            mock_aggregate.return_value = {
                "incident_id": self.incident_id,
                "status": "AGGREGATED"
            }

            result = mock_aggregate(
                [random_raw_event],
                exception=random_exception_str,
                traceback_str=random_traceback_str
            )

            mock_aggregate.assert_called_once_with(
                [random_raw_event],
                exception=random_exception_str,
                traceback_str=random_traceback_str
            )
            self.assertEqual(result["incident_id"], self.incident_id)


if __name__ == "__main__":
    unittest.main()