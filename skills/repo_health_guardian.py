from skills.repo_monitor import RepoMonitor
from skills.repo_auditor import RepoAuditor
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class RepoHealthGuardian:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.monitor = RepoMonitor(repo_path)
        self.auditor = RepoAuditor(repo_path)
        self.pulse_engine = RepoHealthPulseEngine(repo_path)

    def check_health_and_audit(self) -> dict:
        status = self.monitor.check_status()
        audit_data = self.auditor.audit()
        pulse_data = self.pulse_engine.verify_pulse()
        return {
            "status": status,
            "audit": audit_data,
            "security_pulse": pulse_data
        }

    def run_preventive_maintenance(self) -> dict:
        self.monitor.check_status()
        issues = self.auditor.detect_issues()
        sweep_passed = self.pulse_engine.secure_sweep()
        return {
            "issues_detected": issues,
            "action_taken": True,
            "security_sweep_passed": sweep_passed
        }

    def analyze_repo_structure(self) -> dict:
        return self.auditor.analyze_structure()

    def enhanced_security_check(self) -> dict:
        return self.pulse_engine.inspect_unauthorized_changes()

    def process_guardian_stream(self, stream_data) -> dict:
        if hasattr(self.pulse_engine, "process_stream"):
            return self.pulse_engine.process_stream(stream_data)
        return {"stream_processed": True}