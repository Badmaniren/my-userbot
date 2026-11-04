from io import BytesIO
from skills.repo_health_guardian import RepoHealthGuardian
from skills.repo_recovery import RepoRecovery


class RepoHealthRestorer:
    """Модуль комплексного восстановления репозитория,

    объединяющий функционал защиты здоровья и восстановления данных.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.guardian = RepoHealthGuardian(self.repo_path)
        self.recovery = RepoRecovery(self.repo_path)

    def restore_and_protect(self) -> dict:
        maintenance_report = self.guardian.run_preventive_maintenance()
        recovery_status = self.recovery.recover_repository()
        return {
            "recovery_status": recovery_status,
            "maintenance_report": maintenance_report,
        }

    def comprehensive_health_restoration(self, stream) -> dict:
        if isinstance(stream, str):
            stream = BytesIO(stream.encode("utf-8"))
        structure_analysis = self.guardian.analyze_repo_structure()
        restored = self.recovery.safe_restore(stream)
        return {
            "restored": restored,
            "structure_analysis": structure_analysis,
        }

    def execute_restoration_routine(self) -> bool:
        self.guardian.check_health_and_audit()
        status = self.recovery.recover_repository()
        return status