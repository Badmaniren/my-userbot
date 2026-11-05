import os
from skills.dependency_audit_aggregator import aggregate_dependencies
from skills.repo_reporter import RepoReporter

def generate_dependency_audit_report(repo_path, output_report_name, cve_identifier, target_version):
    """
    Комбинирует агрегацию зависимостей и репо-репортер для создания детального отчета по аудиту.
    """
    aggregation_data = aggregate_dependencies(
        repo_path,
        output_report_name,
        cve_identifier,
        target_version
    )

    reporter = RepoReporter(repo_path)
    final_report = reporter.generate_final_report()

    report_path = os.path.join(repo_path, output_report_name)
    saved_path = reporter.save_report(report_path, final_report)

    return {
        "report_path": saved_path if saved_path is not None else report_path,
        "aggregation_data": aggregation_data,
        "final_report": final_report
    }

def generate_audit_report(repo_path, branch, stream_source, output_report_name, cve_identifier, target_version):
    """
    Интеграционная обертка для совместимости с интеграционными тестами.
    """
    aggregation_data = aggregate_dependencies(
        repo_path,
        output_report_name,
        cve_identifier,
        target_version
    )

    reporter = RepoReporter(repo_path)
    final_report = reporter.generate_final_report()

    report_path = os.path.join(repo_path, output_report_name)
    reporter.save_report(report_path, final_report)

    return final_report