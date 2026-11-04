from skills.repo_monitor import RepoMonitor
from skills.repo_auditor import RepoAuditor

class RepoHealthGuardian:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.monitor = RepoMonitor(repo_path)
        self.auditor = RepoAuditor(repo_path)

    def check_health_and_audit(self) -> dict:
        status = self.monitor.check_status()
        audit_data = self.auditor.audit()
        return {
            "status": status,
            "audit": audit_data
        }

    def run_preventive_maintenance(self) -> dict:
        self.monitor.check_status()
        issues = self.auditor.detect_issues()
        return {
            "issues_detected": issues,
            "action_taken": True
        }

    def analyze_repo_structure(self) -> dict:
        return self.auditor.analyze_structure()