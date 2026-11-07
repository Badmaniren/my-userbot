from skills.repo_auditor import RepoAuditor
from skills.repo_audit_synthesizer import RepoAuditSynthesizer

class RepoAuditPipeline:
    def __init__(self, repository_path, output_dir=None, export_stream=None):
        self.repository_path = repository_path
        self.output_dir = output_dir
        self.export_stream = export_stream
        
        self.auditor = RepoAuditor(self.repository_path)
        self.synthesizer = RepoAuditSynthesizer()

    def execute(self):
        audit_result = None
        for method_name in ["audit_repository", "audit", "calculate_metrics"]:
            if hasattr(self.auditor, method_name):
                audit_result = getattr(self.auditor, method_name)()
                break
        
        if audit_result is None and hasattr(self.auditor, "audit_repository"):
            audit_result = self.auditor.audit_repository()

        synthesis_result = self.synthesizer.synthesize(audit_result)
        
        if self.export_stream is not None:
            if hasattr(self.synthesizer, "export_report"):
                try:
                    self.synthesizer.export_report(synthesis_result, self.export_stream)
                except TypeError:
                    self.synthesizer.export_report(self.export_stream)
            elif hasattr(self.synthesizer, "export"):
                self.synthesizer.export(self.export_stream)

        return synthesis_result

    def process_stream(self, stream):
        self.export_stream = stream

def run_audit_pipeline(repository_path, output_dir=None, export_stream=None):
    pipeline = RepoAuditPipeline(
        repository_path=repository_path,
        output_dir=output_dir,
        export_stream=export_stream
    )
    return pipeline.execute()