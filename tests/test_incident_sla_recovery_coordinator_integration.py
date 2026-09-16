import unittest
import uuid
import random
import datetime
from skills.incident_sla_recovery_coordinator import IncidentSLARecoveryCoordinator
from skills.incident_sla_tracker import IncidentSLATracker
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentSLARecoveryCoordinatorIntegration(unittest.TestCase):
    def test_coordinate_recovery_cycle_integration(self):
        incident_id = str(uuid.uuid4())
        module_name = f"module_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        now = datetime.datetime.now(datetime.timezone.utc)
        created_at = now - datetime.timedelta(hours=5)

        sla_thresholds = {severity: 3600}
        
        coordinator = IncidentSLARecoveryCoordinator(
            sla_thresholds=sla_thresholds,
            warning_threshold_pct=0.5
        )

        reg_res = coordinator.register_incident_to_track(
            incident_id=incident_id,
            severity=severity,
            created_at=created_at
        )
        self.assertIsNotNone(reg_res)

        time_to_breach = coordinator.get_current_time_to_breach(incident_id, now)
        self.assertIsInstance(time_to_breach, (int, float))

        recovery_results = coordinator.coordinate_recovery_cycle(current_time=now)
        self.assertIsInstance(recovery_results, list)

        telemetry = coordinator.evaluate_coordinator_telemetry()
        self.assertIsInstance(telemetry, dict)


if __name__ == "__main__":
    unittest.main()