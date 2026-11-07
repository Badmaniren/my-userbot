from skills.repo_auditor import RepoAuditor
from skills.repo_audit_synthesizer import RepoAuditSynthesizer

def start_new(repo_path, output_dir, stream):
    pass

class RepoAuditCollector:
    def __init__(self, repository_path, output_dir=None):
        self.repo_path = repository_path
        self.output_dir = output_dir
        self.auditor = RepoAuditor(repository_path)
        self.synthesizer = RepoAuditSynthesizer()

    def collect_metrics(self):
        return self.auditor.calculate_metrics()

    def collect_and_aggregate(self):
        metrics = self.auditor.calculate_metrics()
        issues = self.auditor.detect_issues()
        structure = self.auditor.analyze_structure()
        
        audit_data = {
            "metrics": metrics,
            "issues": issues,
            "structure": structure
        }
        
        synthesis = self.synthesizer.synthesize(audit_data)
        
        # Поддержка вызова export_report с разным числом аргументов (в зависимости от реализации синтезатора)
        import inspect
        sig = inspect.signature(self.synthesizer.export_report)
        if len(sig.parameters) >= 2:
            export_path = self.synthesizer.export_report(synthesis, self.output_dir if self.output_dir else "report.json")
        else:
            export_path = self.synthesizer.export_report(synthesis)
        
        return {
            "metrics": metrics,
            "issues": issues,
            "structure": structure,
            "synthesis": synthesis,
            "export_path": export_path,
            "audit_metrics": metrics,
            "synthesis_result": synthesis
        }

    def run_external_synthesizer(self, stream):
        return start_new(self.repo_path, self.output_dir, stream)

    def process_audit_stream(self, stream):
        return self.auditor.process_log_stream(stream)

    def export_aggregated_report(self, filename="report.json"):
        import os
        data = self.collect_and_aggregate()
        target_dir = self.output_dir if self.output_dir else "."
        
        import inspect
        sig = inspect.signature(self.synthesizer.export_report)
        if len(sig.parameters) >= 2:
            export_path = self.synthesizer.export_report(data, os.path.join(target_dir, filename))
        else:
            export_path = self.synthesizer.export_report(data)
            
        return export_path