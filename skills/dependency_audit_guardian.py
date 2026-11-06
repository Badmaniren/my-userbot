from skills import dependency_audit_aggregator
from skills import dependency_audit_validator

def start_new(repo, branch, stream):
    return dependency_audit_aggregator.start_new(repo, branch, stream)

def start_new_audit(repo, branch, stream):
    return dependency_audit_aggregator.start_new(repo, branch, stream)

def execute_guarded_audit(repo, report, cve, version, branch, stream):
    return dependency_audit_validator.validate_and_aggregate_dependencies(
        repo, report, cve, version, branch, stream
    )

def apply_audit_data(chaos_bytes):
    return dependency_audit_validator.validate_and_apply_audit(chaos_bytes)

def validate_and_aggregate_dependencies(repo_path, output_report_name, cve_identifier, target_version, branch, stream_source):
    return dependency_audit_validator.validate_and_aggregate_dependencies(
        repo_path, output_report_name, cve_identifier, target_version, branch, stream_source
    )