from skills.repo_health_dispatcher import RepoHealthDispatcher
from skills.repo_audit_synthesizer import RepoAuditSynthesizer


class RepoAuditDispatcher:
    def __init__(self, repository_path: str, output_dir: str, export_stream=None):
        self.repository_path = repository_path
        self.output_dir = output_dir
        self.export_stream = export_stream
        
        self.health_dispatcher = RepoHealthDispatcher(repo_path=repository_path)
        self.synthesizer = RepoAuditSynthesizer()

    def dispatch_health_checks(self, file_path: str) -> bool:
        return self.health_dispatcher.dispatch()

    def dispatch_health(self, file_path: str) -> bool:
        return self.health_dispatcher.dispatch()

    def dispatch_critical_check(self, title: str, value, file_path: str) -> bool:
        return self.health_dispatcher.check_and_notify_critical(title, value, file_path)

    def check_critical_metric(self, title: str, value, file_path: str) -> bool:
        return self.health_dispatcher.check_and_notify_critical(title, value, file_path)

    def run_synthesis(self, payload: dict) -> dict:
        return self.synthesizer.synthesize(payload)

    def run_full_synthesis(self, payload: dict) -> dict:
        return self.synthesizer.synthesize(payload)

    def export_audit_report(self, target_path, synthesis_result, filename=None) -> str:
        if filename is None:
            filename = synthesis_result
            synthesis_result = target_path
            target_path = self.output_dir
        return self.synthesizer.export_report(target_path, synthesis_result, filename)

    def run_complete_audit_workflow(self, file_path: str, payload: dict, export_filename: str) -> dict:
        health_dispatched = self.health_dispatcher.dispatch()
        synthesis_data = self.synthesizer.synthesize(payload)
        export_path = self.synthesizer.export_report(self.output_dir, synthesis_data, export_filename)
        
        return {
            "health_dispatched": health_dispatched,
            "synthesis_data": synthesis_data,
            "export_path": export_path
        }

    def process_audit_stream(self, stream, file_path: str) -> bool:
        return self.health_dispatcher.process_stream_and_dispatch(stream, file_path)