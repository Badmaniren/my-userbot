from skills.anomaly_autofixer_worker import (
    AnomalyAutofixerWorker,
    AutofixerWorkerError,
    PatchApplicationError,
)
from skills.anomaly_rollback_controller import (
    AnomalyRollbackController,
    AnomalyRollbackControllerError,
)


class AnomalyRemediatorError(Exception):
    """Базовое исключение для AnomalyRemediator."""
    pass


class AnomalyRemediator:
    def __init__(
        self,
        repo_path: str = ".",
        log_path: str = "remediator.log",
        worker_id: str = "default_worker",
        threshold: float = 0.5,
    ):
        self.repo_path = repo_path
        self.log_path = log_path
        self.worker_id = worker_id
        self.threshold = threshold

        self.autofixer = AnomalyAutofixerWorker(
            worker_id=self.worker_id,
            repo_path=self.repo_path,
            log_path=self.log_path,
        )
        self.rollback_controller = AnomalyRollbackController(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
        )

    def remediate_anomaly(
        self,
        anomaly_id: str,
        patch_id: str,
        patch_content: str,
        target_file: str,
        verification_command: str,
        source: str,
    ) -> dict:
        try:
            details = self.autofixer.process_autofix(
                anomaly_id,
                patch_id,
                patch_content,
                target_file,
                verification_command,
            )
            return {
                "status": "success",
                "details": details,
            }
        except (PatchApplicationError, AutofixerWorkerError) as e:
            try:
                rollback_success = self.rollback_controller.execute_rollback(anomaly_id, source)
            except AnomalyRollbackControllerError as rbe:
                raise AnomalyRemediatorError(f"Rollback failed: {rbe}") from rbe

            return {
                "status": "rolled_back",
                "rollback_success": rollback_success,
                "error": str(e),
            }

    def apply_and_verify(
        self,
        anomaly_id: str,
        patch_id: str,
        patch_content: str,
        target_file: str,
        verification_command: str,
        source: str,
    ) -> dict:
        try:
            applied = self.autofixer.apply_patch(patch_id, patch_content, target_file)
            verified = self.autofixer.verify_fix(anomaly_id, verification_command)
            if applied and verified:
                return {"status": "success"}
            else:
                self.rollback_controller.execute_rollback(anomaly_id, source)
                return {"status": "failed_verification_rolled_back"}
        except (PatchApplicationError, AutofixerWorkerError) as e:
            try:
                self.rollback_controller.execute_rollback(anomaly_id, source)
            except AnomalyRollbackControllerError as rbe:
                raise AnomalyRemediatorError(f"Rollback failed: {rbe}") from rbe
            return {"status": "failed_verification_rolled_back"}

    def force_rollback(self, anomaly_id: str, source: str) -> dict:
        try:
            rollback_success = self.rollback_controller.execute_rollback(anomaly_id, source)
            epic_summary = self.rollback_controller.finalize_epic_restoration()
            return {
                "success": rollback_success,
                "epic_summary": epic_summary,
            }
        except AnomalyRollbackControllerError as e:
            raise AnomalyRemediatorError(str(e)) from e

    def remediate(
        self,
        anomaly_id: str,
        patch_id: str,
        patch_content: str,
        target_file: str,
        verification_command: str,
        source: str,
    ) -> dict:
        try:
            res = self.apply_and_verify(
                anomaly_id=anomaly_id,
                patch_id=patch_id,
                patch_content=patch_content,
                target_file=target_file,
                verification_command=verification_command,
                source=source,
            )
            return res
        except Exception as e:
            try:
                self.rollback_controller.execute_rollback(anomaly_id, source)
            except AnomalyRollbackControllerError as rbe:
                raise AnomalyRemediatorError(f"Rollback failed during remediation error handling: {rbe}") from rbe
            return {
                "status": "rolled_back",
                "rollback": True,
                "error": str(e),
            }