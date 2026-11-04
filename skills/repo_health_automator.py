from skills.repo_monitor import RepoMonitor
from skills.repo_health_guardian import RepoHealthGuardian

class RepoHealthAutomator:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.monitor = RepoMonitor(repo_path)
        self.guardian = RepoHealthGuardian(repo_path)

    def automate_health_and_maintenance(self) -> dict:
        monitor_status = self.monitor.check_status()
        health_audit = self.guardian.check_health_and_audit()
        preventive_maintenance = self.guardian.run_preventive_maintenance()

        return {
            "monitor_status": monitor_status,
            "health_audit": health_audit,
            "preventive_maintenance": preventive_maintenance
        }

    def process_stream_and_automate(self, stream) -> dict:
        # Читаем данные из потока для учета в процессе (если требуется)
        _ = stream.read()
        
        monitor_status = self.monitor.check_status()
        health_audit = self.guardian.check_health_and_audit()
        preventive_maintenance = self.guardian.run_preventive_maintenance()

        return {
            "monitor_status": monitor_status,
            "health_audit": health_audit,
            "preventive_maintenance": preventive_maintenance
        }

    def run(self) -> dict:
        return self.automate_health_and_maintenance()

    def automate_health_check(self) -> dict:
        return self.automate_health_and_maintenance()