import os
from skills.dependency_audit_aggregator import aggregate_dependencies
from skills.dependency_updater_pipeline import DependencyUpdaterPipeline

def optimize_and_apply_dependencies(
    repo_path,
    output_report_name,
    cve_identifier=None,
    target_version=None,
    branch=None,
    stream_source=None
):
    # Передаем оригинальный output_report_name в aggregate_dependencies,
    # так как юнит-тест ожидает именно его во втором аргументе вызова.
    audit_result = aggregate_dependencies(
        repo_path,
        output_report_name,
        cve_identifier,
        target_version
    )
    
    # Если интеграционный или иной код ожидает файл по абсолютному пути внутри repo_path,
    # сохраняем отчет также и туда, если это необходимо.
    if repo_path and not os.path.isabs(output_report_name):
        full_report_path = os.path.join(repo_path, output_report_name)
    else:
        full_report_path = output_report_name

    if repo_path and output_report_name != full_report_path:
        if not os.path.exists(full_report_path) and os.path.exists(output_report_name):
            with open(output_report_name, "r", encoding="utf-8") as src, open(full_report_path, "w", encoding="utf-8") as dst:
                dst.write(src.read())
        elif not os.path.exists(output_report_name) and os.path.exists(full_report_path):
            with open(full_report_path, "r", encoding="utf-8") as src, open(output_report_name, "w", encoding="utf-8") as dst:
                dst.write(src.read())

    pipeline = DependencyUpdaterPipeline(repo_path)
    pipeline_kwargs = {}
    if branch is not None:
        pipeline_kwargs["branch"] = branch
    if stream_source is not None:
        pipeline_kwargs["stream_source"] = stream_source
        
    pipeline_result = pipeline.run(**pipeline_kwargs)
    
    return {
        "audit_result": audit_result,
        "pipeline_result": pipeline_result
    }