from skills.incident_aggregator import IncidentAggregator
from skills.dependency_audit_reporter import DependencyAuditReporter


class RecoveryReportExporter:
    """Модуль объединяет агрегатор инцидентов и репортер зависимостей

    для формирования и экспорта комплексных отчетов по самовосстановлению системы.
    """

    def __init__(self):
        self.aggregator = IncidentAggregator()
        self.reporter = DependencyAuditReporter()

    def generate_comprehensive_report(
        self, module_name, exception, traceback_str, incident_id, audit_data
    ):
        aggregated_result = self.aggregator.process_and_aggregate(
            module_name, exception, traceback_str, incident_id
        )
        report_output = self.reporter.generate_report(audit_data)

        return {
            "incident_analytics": aggregated_result,
            "dependency_report": report_output,
        }

    def finalize_and_export_summary(
        self, epic_id, stream=None, summary_payload=None, export_format="json"
    ):
        finalized = self.reporter.finalize_epic(epic_id, stream)
        export_result = self.reporter.export_summary(summary_payload, export_format)

        return {"epic_finalized": finalized, "summary_export": export_result}

    def export_epic_report_file(self, report_payload, output_path):
        return self.reporter.generate_epic_report(report_payload, output_path)