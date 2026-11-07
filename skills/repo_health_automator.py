from skills.repo_health_diagnostic import RepoHealthDiagnostic
from skills.repo_health_restorer import RepoHealthRestorer

class RepoHealthAutomator:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.diagnostic = RepoHealthDiagnostic()
        self.restorer = RepoHealthRestorer(repo_path)

    def automate_health_and_maintenance(self) -> dict:
        monitor_status = self.diagnostic.run_full_diagnostic(self.repo_path)
        health_audit = self.restorer.restore_and_protect()
        preventive_maintenance = {"status": "ok"}

        return {
            "monitor_status": monitor_status,
            "health_audit": health_audit,
            "preventive_maintenance": preventive_maintenance
        }

    def process_stream_and_automate(self, stream) -> dict:
        stream_data = stream.read()
        
        monitor_status = self.diagnostic.run_full_diagnostic(self.repo_path)
        health_audit = self.restorer.comprehensive_health_restoration(stream_data)
        preventive_maintenance = {"status": "ok"}

        return {
            "monitor_status": monitor_status,
            "health_audit": health_audit,
            "preventive_maintenance": preventive_maintenance
        }

    def run(self) -> dict:
        return self.automate_health_and_maintenance()

    def automate_health_check(self) -> dict:
        return self.automate_health_and_maintenance()