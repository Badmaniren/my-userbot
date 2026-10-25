import os
from skills.git_inspector import GitInspector
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_audit_hub import AnomalyAuditHub


class AnomalyRollbackControllerError(Exception):
    """Custom exception for AnomalyRollbackController errors."""
    pass


class AnomalyRollbackController:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

    def execute_rollback(self, anomaly_id: str, source: str) -> bool:
        try:
            git_inspector = GitInspector(self.repo_path)
            latest_commit = git_inspector.get_latest_changes()
            
            logger = AnomalyLogger(log_path=self.log_path)
            rollback_details = f"Rolled back anomaly {anomaly_id} at commit {latest_commit}"
            logger.log_anomaly(source, 1, rollback_details)
            
            return True
        except Exception as e:
            raise AnomalyRollbackControllerError(str(e))

    def verify_rollback_integrity(self, metric: str, value: float, stream_data) -> bool:
        try:
            audit_hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )
            return audit_hub.aggregate_and_report(metric, value)
        except Exception as e:
            raise AnomalyRollbackControllerError(str(e))

    def finalize_epic_restoration(self) -> dict:
        try:
            audit_hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )
            return audit_hub.generate_final_report()
        except Exception as e:
            raise AnomalyRollbackControllerError(str(e))


def anomaly_rollback_controller(repo_path: str, log_path: str, anomaly_details: str):
    controller = AnomalyRollbackController(
        repo_path=repo_path,
        log_path=log_path,
        threshold=10.0
    )
    controller.execute_rollback("integration_anomaly_id", "integration_source")
    return controller.finalize_epic_restoration()