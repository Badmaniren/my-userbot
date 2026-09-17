import unittest
import uuid
import random
import datetime
from skills.incident_sla_recovery_coordinator import IncidentSLARecoveryCoordinator
from skills.incident_sla_tracker import IncidentSLATracker
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher

class TestIncidentSLARecoveryCoordinatorIntegration(unittest.TestCase):
    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.module_name = f"module_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.created_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)

        thresholds = {self.severity: 3600}
        self.coordinator = IncidentSLARecoveryCoordinator(
            sla_thresholds=thresholds,
            warning_threshold_pct=0.5
        )

    def test_integration_sla_recovery_lifecycle(self):
        register_res = self.coordinator.register_incident_to_track(
            incident_id=self.incident_id,
            severity=self.severity,
            created_at=self.created_at
        )
        self.assertIsNotNone(register_res)
        self.assertIn("incident_id", register_res)
        self.assertEqual(register_res["incident_id"], self.incident_id)

        current_time = datetime.datetime.now(datetime.timezone.utc)
        time_to_breach = self.coordinator.get_current_time_to_breach(
            incident_id=self.incident_id,
            current_time=current_time
        )
        self.assertIsInstance(time_to_breach, (int, float))

        recovery_results = self.coordinator.coordinate_recovery_cycle(
            current_time=current_time
        )
        self.assertIsInstance(recovery_results, list)

        exception_msg = f"Runtime failure in {self.module_name}"
        failure_result = self.coordinator.coordinate_recovery_for_incident(
            incident_id=self.incident_id,
            module_name=self.module_name,
            exception=Exception(exception_msg)
        )
        self.assertIsInstance(failure_result, dict)
        self.assertEqual(failure_result.get("incident_id"), self.incident_id)
        self.assertIn("dispatch_result", failure_result)

        telemetry = self.coordinator.evaluate_coordinator_telemetry()
        self.assertIsInstance(telemetry, (dict, list))

if __name__ == "__main__":
    unittest.main()