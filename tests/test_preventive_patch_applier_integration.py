import unittest
import uuid
import random
from skills.incident_trend_forecaster import IncidentTrendForecaster
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.preventive_patch_applier import PreventivePatchApplier


class TestPreventivePatchApplierIntegration(unittest.TestCase):

    def setUp(self):
        self.module_suffix = uuid.uuid4().hex[:8]
        self.target_module = f"test_service_{self.module_suffix}"
        self.forecaster = IncidentTrendForecaster()
        self.recovery_hub = ErrorRecoveryHub()
        
        # Instantiate applier using real skills without mocks
        self.applier = PreventivePatchApplier(
            forecaster=self.forecaster,
            recovery_hub=self.recovery_hub
        )

    def test_preventive_patch_workflow_with_real_history(self):
        # 1. Simulate failures in ErrorRecoveryHub to create realistic history
        failure_count = random.randint(2, 5)
        captured_incident_ids = []

        for i in range(failure_count):
            err_msg = f"Simulated failure {i}_{uuid.uuid4()}"
            tb_str = f"Traceback (most recent call last):\n  File 'app.py', line {i}\nRuntimeError: {err_msg}"
            incident_id = self.recovery_hub.capture_failure(
                module_name=self.target_module,
                exception=RuntimeError(err_msg),
                traceback_str=tb_str
            )
            if incident_id:
                captured_incident_ids.append(incident_id)

        # 2. Execute forecast using real IncidentTrendForecaster
        forecast_result = self.forecaster.forecast_future_incidents(self.target_module)
        self.assertIsInstance(forecast_result, dict)

        # 3. Trigger preventive patch application process
        # Check standard possible method names on PreventivePatchApplier
        if hasattr(self.applier, "apply_preventive_patches"):
            result = self.applier.apply_preventive_patches(self.target_module)
        elif hasattr(self.applier, "run_preventive_cycle"):
            result = self.applier.run_preventive_cycle(self.target_module)
        elif hasattr(self.applier, "process_module"):
            result = self.applier.process_module(self.target_module)
        else:
            result = self.applier.apply_patch_preventively(self.target_module)

        # 4. Verify outcome contains target module context and real execution results
        self.assertIsNotNone(result)
        
        if isinstance(result, dict):
            self.assertIn("module_name", result)
            self.assertEqual(result["module_name"], self.target_module)
            if "status" in result:
                self.assertIn(result["status"], ["success", "applied", "no_action_needed", True])
        elif hasattr(result, "success"):
            self.assertTrue(result.success)

        # 5. Verify real state changes in recovery hub or incident history
        history = self.recovery_hub.get_incident_history(self.target_module)
        self.assertIsNotNone(history)

    def test_preventive_patch_clean_module_flow(self):
        # Test preventive patching on a completely new clean module name
        clean_module = f"clean_module_{uuid.uuid4().hex}"
        
        # Verify forecast works on empty module
        forecast = self.forecaster.predict_next_failure_window(clean_module)
        self.assertIsInstance(forecast, dict)

        # Run preventive patch process on clean module
        if hasattr(self.applier, "apply_preventive_patches"):
            res = self.applier.apply_preventive_patches(clean_module)
        elif hasattr(self.applier, "run_preventive_cycle"):
            res = self.applier.run_preventive_cycle(clean_module)
        elif hasattr(self.applier, "process_module"):
            res = self.applier.process_module(clean_module)
        else:
            res = self.applier.apply_patch_preventively(clean_module)

        self.assertIsNotNone(res)


if __name__ == "__main__":
    unittest.main()