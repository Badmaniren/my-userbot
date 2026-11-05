import os
from typing import Any
from skills.dependency_audit_aggregator import aggregate_dependencies
from skills.dependency_audit_reporter import DependencyAuditReporter


class DependencyAuditExporter:
    """
    Модуль для экспорта агрегированных данных аудита зависимостей
    в структурированные форматы для внешней отчетности.
    """
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def export_audit_data(
        self,
        branch: str,
        stream_source: str,
        output_report_name: str,
        cve_identifier: str,
        target_version: str
    ):
        # Агрегация данных
        aggregate_dependencies(
            repo_path=self.repo_path,
            output_report_name=output_report_name,
            cve_identifier=cve_identifier,
            target_version=target_version
        )
        reporter = DependencyAuditReporter(repo_path=self.repo_path)
        return reporter.generate_audit_report(
            branch=branch,
            stream_source=stream_source,
            output_report_name=output_report_name,
            cve_identifier=cve_identifier,
            target_version=target_version
        )

    def export_custom_report(self, status: str, summary: dict, output_path: str):
        reporter = DependencyAuditReporter(repo_path=self.repo_path)
        return reporter.create_custom_report(
            status=status,
            summary=summary,
            output_path=output_path
        )

    def save_exported_report(self, file_path: str, report_content: Any):
        reporter = DependencyAuditReporter(repo_path=self.repo_path)
        return reporter.save_audit_report(
            file_path=file_path,
            report_content=report_content
        )


def export_dependency_audit(
    repo_path: str,
    branch: str,
    stream_source: str,
    output_report_name: str,
    cve_identifier: str,
    target_version: str
):
    exporter = DependencyAuditExporter(repo_path=repo_path)
    result = exporter.export_audit_data(
        branch=branch,
        stream_source=stream_source,
        output_report_name=output_report_name,
        cve_identifier=cve_identifier,
        target_version=target_version
    )

    report_path = (
        result
        if result and isinstance(result, str) and os.path.exists(result)
        else os.path.join(repo_path, output_report_name)
    )

    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        needs_update = False
        if cve_identifier and cve_identifier not in content:
            content += f"\nCVE: {cve_identifier}\n"
            needs_update = True
        if target_version and target_version not in content:
            content += f"\nVersion: {target_version}\n"
            needs_update = True

        if needs_update:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)

    return result or report_path
