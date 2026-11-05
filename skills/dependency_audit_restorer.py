from skills import dependency_audit_aggregator
from skills.repo_recovery import RepoRecovery


class DependencyAuditRestorer:
    """Модуль автоматического отката или восстановления зависимостей."""

    def __init__(self, repo_path: str, branch: str, stream_source: str):
        self.repo_path = repo_path
        self.branch = branch
        self.stream_source = stream_source

    def audit_and_restore(self, output_report_name: str, cve_identifier: str, target_version: str) -> bool:
        audit_result = dependency_audit_aggregator.aggregate_dependencies(
            self.repo_path,
            output_report_name,
            cve_identifier,
            target_version
        )
        
        status = audit_result.get("status")
        if status == "CRITICAL":
            recovery = RepoRecovery(self.repo_path)
            return recovery.recover_repository()
        
        return True

    def execute_safe_restore(self, stream_io) -> bool:
        recovery = RepoRecovery(self.repo_path)
        return recovery.safe_restore(stream_io)

    def run_new_audit(self) -> dict:
        return dependency_audit_aggregator.start_new(
            self.repo_path,
            self.branch,
            self.stream_source
        )


def audit_and_restore_dependencies(repo_path: str, branch: str, stream_source: str, output_report_name: str, cve_identifier: str, target_version: str) -> bool:
    restorer = DependencyAuditRestorer(repo_path=repo_path, branch=branch, stream_source=stream_source)
    return restorer.audit_and_restore(output_report_name, cve_identifier, target_version)