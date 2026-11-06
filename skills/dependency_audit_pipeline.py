from skills import dependency_audit_guardian
from skills.dependency_audit_reporter import DependencyAuditReporter


def run_dependency_audit_pipeline(
    repo_path: str,
    branch: str,
    stream_source: str,
    cve_identifier: str,
    target_version: str,
    output_report_name: str
) -> bool:
    """
    Объединяет функции контроля безопасности зависимостей (guardian) 
    и построения отчетов (reporter) в единый завершающий пайплайн аудита.
    """
    guardian_success = dependency_audit_guardian.execute_guarded_audit(
        repo=repo_path,
        report=output_report_name,
        cve=cve_identifier,
        version=target_version,
        branch=branch,
        stream=stream_source
    )

    if not guardian_success:
        return False

    try:
        reporter = DependencyAuditReporter(repo_path=repo_path)
        report_generated = reporter.generate_audit_report(
            branch=branch,
            stream_source=stream_source,
            output_report_name=output_report_name,
            cve_identifier=cve_identifier,
            target_version=target_version
        )
        return bool(report_generated)
    except Exception:
        return False