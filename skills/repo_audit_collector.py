from skills.repo_auditor import RepoAuditor
from skills.repo_audit_synthesizer import RepoAuditSynthesizer
import os

def start_new(repo_path, output_dir, stream):
    return RepoAuditSynthesizer().export_report(stream, os.path.join(output_dir if output_dir else ".", "report.json"))

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
        
        target_dir = self.output_dir if self.output_dir else "."
        os.makedirs(target_dir, exist_ok=True)
        export_path = os.path.join(target_dir, "report.json")
        self.synthesizer.export_report(synthesis, export_path)
        
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
        data = self.collect_and_aggregate()
        target_dir = self.output_dir if self.output_dir else "."
        os.makedirs(target_dir, exist_ok=True)
        export_path = os.path.join(target_dir, filename)
        
        synthesis = data.get("synthesis", data)
        self.synthesizer.export_report(synthesis, export_path)
            
        return export_path