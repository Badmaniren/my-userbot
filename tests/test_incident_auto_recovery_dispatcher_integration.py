import unittest
import uuid
import random
import sys
import os

from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine


class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.recovery_hub = ErrorRecoveryHub()
        self.escalation_engine = IncidentAutoEscalationEngine()
        
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        self.random_module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.random_error_message = f"Critical failure in subsystem {random.randint(1000, 9999)}"

    def test_end_to_end_auto_recovery_dispatch(self):
        try:
            raise RuntimeError(self.random_error_message)
        except RuntimeError as e:
            tb_str = "".join(sys.exc_info())
            
            captured_incident = self.recovery_hub.capture_failure(
                module_name=self.random_module_name,
                exception=e,
                traceback_str=tb_str
            )
            
            incident_id = captured_incident.get("incident_id", self.random_incident_id) if isinstance(captured_incident, dict) else self.random_incident_id

            dispatch_result = self.dispatcher.dispatch_recovery(
                incident_id=incident_id,
                module_name=self.random_module_name,
                exception=e
            )

            self.assertIsNotNone(dispatch_result, "Dispatcher returned None for recovery process")
            
            escalation_status = self.escalation_engine.process_escalation(incident_id)
            self.assertIsInstance(escalation_status, dict, "Escalation engine must return a dictionary status")

            history = self.recovery_hub.get_incident_history(self.random_module_name)
            self.assertIsNotNone(history, "Incident history should not be empty after dispatch")


    def test_telemetry_risk_evaluation_and_patch_trigger(self):
        telemetry_risks = self.escalation_engine.evaluate_system_telemetry_risks()
        self.assertIsInstance(telemetry_risks, dict, "Telemetry risks evaluation must return structured data")

        patch_triggered = self.escalation_engine.check_and_trigger_patching()
        self.assertIn(patch_triggered, [True, False], "Patch triggering check must evaluate to boolean")

        context_data = {
            "random_seed": random.randint(1, 100000),
            "telemetry_state": telemetry_risks
        }

        recovery_action = self.recovery_hub.analyze_and_recover(
            module_name=self.random_module_name,
            exception=ValueError(f"Random validation error {uuid.uuid4()}"),
            context=context_data
        )

        self.assertIsNotNone(recovery_action, "Analyze and recover workflow must execute and return result")


if __name__ == "__main__":
    unittest.main()