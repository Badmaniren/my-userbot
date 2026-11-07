import os
from skills.repo_monitor import RepoMonitor
from skills.repo_audit_synthesizer import RepoAuditSynthesizer

def start_new(repository_path, output_dir, export_stream):
    """
    Вспомогательная функция для запуска внешних процессов или инициализации потока экспорта,
    ожидаемая юнит-тестами.
    """
    pass

class RepoAuditAggregatorPipeline:
    def __init__(self, repository_path, output_dir):
        self.repository_path = repository_path
        self.output_dir = output_dir
        self.monitor = RepoMonitor(self.repository_path)
        self.synthesizer = RepoAuditSynthesizer()

    def run(self, export_stream=None, filename="report.json", synthetic_payload=None):
        try:
            start_new(
                repository_path=self.repository_path,
                output_dir=self.output_dir,
                export_stream=export_stream
            )
        except Exception as e:
            raise e

        monitor_status = self.monitor.check_status()
        
        payload = {"monitor_status": monitor_status}
        if synthetic_payload and isinstance(synthetic_payload, dict):
            payload.update(synthetic_payload)

        synthesis_result = self.synthesizer.synthesize(payload)

        os.makedirs(self.output_dir, exist_ok=True)
        export_path = self.synthesizer.export_report(
            target_path=self.output_dir,
            synthesis_result=synthesis_result,
            filename=filename
        )

        return {
            "monitor_status": monitor_status,
            "monitor": monitor_status,
            "synthesis": synthesis_result,
            "export_path": export_path
        }


def run_audit_aggregation(repository_path, output_dir, export_stream=None, filename="report.json", synthetic_payload=None):
    pipeline = RepoAuditAggregatorPipeline(repository_path=repository_path, output_dir=output_dir)
    return pipeline.run(export_stream=export_stream, filename=filename, synthetic_payload=synthetic_payload)


def run_audit_aggregator_pipeline(repository_path, output_dir, synthetic_payload=None, export_stream=None, filename="report.json"):
    pipeline = RepoAuditAggregatorPipeline(repository_path=repository_path, output_dir=output_dir)
    return pipeline.run(export_stream=export_stream, filename=filename, synthetic_payload=synthetic_payload)