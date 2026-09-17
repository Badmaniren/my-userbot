import random
import time
import unittest
import uuid
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.critical_sla = random.randint(1800, 3600)
        self.high_sla = random.randint(3601, 7200)
        self.warning_pct = round(random.uniform(0.70, 0.85), 2)
        self.sla_thresholds = {
            "CRITICAL": self.critical_sla,
            "HIGH": self.high_sla
        }
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_pct
        )

    def test_register_and_get_time_to_breach_calculation(self):
        incident_id = f"inc-{uuid.uuid4()}"
        base_time = datetime(2025, 1, 1, 10, 0, 0)
        elapsed_seconds = random.randint(100, 1500)
        current_time = base_time + timedelta(seconds=elapsed_seconds)

        self.tracker.register_incident(
            incident_id=incident_id,
            severity="CRITICAL",
            created_at=base_time
        )

        time_to_breach = self.tracker.get_time_to_breach(
            incident_id=incident_id,
            current_time=current_time
        )

        expected_remaining = float(self.critical_sla - elapsed_seconds)
        self.assertEqual(time_to_breach, expected_remaining)

        non_existent_id = f"missing-{uuid.uuid4()}"
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(incident_id=non_existent_id, current_time=current_time)

    def test_check_sla_breaches_and_status_updates(self):
        base_time = datetime(2025, 1, 1, 12, 0, 0)

        ok_id = f"ok-{uuid.uuid4()}"
        ok_created_at = base_time - timedelta(seconds=int(self.critical_sla * self.warning_pct * 0.5))
        self.tracker.register_incident(ok_id, "CRITICAL", ok_created_at)

        warning_id = f"warn-{uuid.uuid4()}"
        warning_created_at = base_time - timedelta(seconds=int(self.critical_sla * (self.warning_pct + 0.05)))
        self.tracker.register_incident(warning_id, "CRITICAL", warning_created_at)

        breach_id = f"breach-{uuid.uuid4()}"
        breach_created_at = base_time - timedelta(seconds=self.critical_sla + random.randint(50, 300))
        self.tracker.register_incident(breach_id, "CRITICAL", breach_created_at)

        breaches = self.tracker.check_sla_breaches(current_time=base_time)
        results_map = {item["incident_id"]: item["status"] for item in breaches}

        self.assertNotIn(ok_id, results_map)
        self.assertIn(warning_id, results_map)
        self.assertEqual(results_map[warning_id], "WARNING")
        self.assertIn(breach_id, results_map)
        self.assertEqual(results_map[breach_id], "BREACHED")

        self.tracker.update_incident_status(breach_id, "RESOLVED")
        breaches_after_resolve = self.tracker.check_sla_breaches(current_time=base_time)
        resolved_results_map = {item["incident_id"]: item["status"] for item in breaches_after_resolve}

        self.assertNotIn(breach_id, resolved_results_map)
        self.assertIn(warning_id, resolved_results_map)

    def test_track_incident_sla_pipeline_flow(self):
        incident_id = f"flow-{uuid.uuid4()}"
        threshold_seconds = random.randint(600, 1800)
        recent_timestamp = time.time() - random.randint(10, 100)

        sla_payload = {
            "incident_id": incident_id,
            "threshold_seconds": threshold_seconds,
            "aggregated_data": {
                "data": {
                    "timestamp": recent_timestamp
                }
            }
        }

        result = track_incident_sla(sla_payload)

        self.assertEqual(result["incident_id"], incident_id)
        self.assertFalse(result["breach_predicted"])
        self.assertGreater(result["time_remaining_seconds"], 0.0)

        past_timestamp = time.time() - (threshold_