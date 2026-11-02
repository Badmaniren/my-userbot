import threading
import logging
import os
from skills.patch_regression_hub import PatchRegressionHub
from skills.patch_applier import PatchApplier
from skills.system_telemetry import SystemTelemetry

class PatchRegressionRunner:
    def __init__(self, repo_path=None, log_path=None):
        self.repo_path = repo_path
        self.log_path = log_path
        self.logger = logging.getLogger(__name__)

    def run_regression_scenario(self, scenario_id, target):
        def wrapper():
            try:
                target()
            except Exception as e:
                self.logger.error(f"Error in scenario {scenario_id}: {str(e)}")
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
        return thread

    def execute_with_audit(self, payload):
        hub = PatchRegressionHub(repo_path=self.repo_path, log_path=self.log_path)
        hub.log_anomaly(payload)

    def capture_state(self):
        telemetry = SystemTelemetry()
        return telemetry.get_snapshot()

    def apply_patch_isolated(self, patch_id):
        applier = PatchApplier(repo_path=self.repo_path)
        applier.apply(patch_id)

    def report_metric(self, metric, value):
        hub = PatchRegressionHub(repo_path=self.repo_path, log_path=self.log_path)
        hub.aggregate_and_report(metric, value)

    def execute_scenario(self, scenario_id, target_path):
        if not os.path.exists(target_path):
            raise Exception("Path does not exist")
        
        # Логика выполнения сценария
        return {
            "status": "success",
            "run_id": scenario_id
        }