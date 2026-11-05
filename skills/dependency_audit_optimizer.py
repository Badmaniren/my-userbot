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
    audit_result = aggregate_dependencies(
        repo_path,
        output_report_name,
        cve_identifier,
        target_version
    )
    
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