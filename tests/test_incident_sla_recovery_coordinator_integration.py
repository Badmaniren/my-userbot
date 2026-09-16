import unittest
import uuid
import random
from datetime import datetime, timezone

from skills.incident_sla_tracker import IncidentSLATracker
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher
from skills.incident_sla_recovery_coordinator import IncidentSLARecoveryCoordinator


class TestIncidentSLARecoveryCoordinatorIntegration(unittest.TestCase):
    
    def test_end_to_end_sla_recovery_orchestration(self):
        incident_id = f"inc-{uuid.uuid4()}"
        module_name = f"module_{uuid.uuid4().hex[:8]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        current_time = datetime.now(timezone.utc)
        created_at = current_time.timestamp()
        
        sla_thresholds = {severity: random.randint(60, 300)}
        tracker = IncidentSLATracker(sla_thresholds=sla_thresholds, warning_threshold_pct=0.8)
        dispatcher = IncidentAutoRecoveryDispatcher()
        
        coordinator = IncidentSLARecoveryCoordinator(
            sla_tracker=tracker,
            recovery_dispatcher=dispatcher
        )
        
        coordinator.register_and_track(
            incident_id=incident_id,
            severity=severity,
            created_at=created_at
        )
        
        time_to_breach = coordinator.get_current_time_to_breach(
            incident_id=incident_id,
            current_time=current_time.timestamp()
        )
        self.assertIsInstance(time_to_breach, float)
        
        exception_msg = f"RuntimeFailure_{uuid.uuid4()}"
        test_exception = RuntimeError(exception_msg)
        
        recovery_result = coordinator.coordinate_recovery_for_incident(
            incident_id=incident_id,
            module_name=module_name,
            exception=test_exception
        )
        
        self.assertIsInstance(recovery_result, dict)
        self.assertIn("dispatch_result", recovery_result)
        self.assertIn("incident_id", recovery_result)
        self.assertEqual(recovery_result["incident_id"], incident_id)
        
        telemetry = coordinator.evaluate_coordinator_telemetry()
        self.assertIsInstance(telemetry, dict)


if __name__ == "__main__":
    unittest.main()