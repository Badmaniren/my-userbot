from datetime import datetime
import json
import sys

class DependencyAuditReporter:
    def __init__(self):
        pass

    def generate_report(self, audit_data: dict) -> str:
        timestamp = datetime.now().isoformat()
        if "error_code" in audit_data:
            err_msg = f"ERROR: code {audit_data['error_code']} at {timestamp}"
            sys.stderr.write(err_msg)
            return err_msg
        
        report_dict = {
            "timestamp": timestamp,
            **audit_data
        }
        return json.dumps(report_dict)

    def finalize_epic(self, epic_id: str, stream) -> bool:
        filename = f"epic_{epic_id}_audit.log"
        data = stream.read()
        with open(filename, "wb") as f:
            f.write(data)
        return True

    def export_summary(self, summary_payload: dict, format: str = "json") -> str:
        return json.dumps(summary_payload)

    def generate_epic_report(self, report_payload: dict, output_path: str) -> bool:
        content = json.dumps(report_payload, indent=2)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

def dependency_audit_reporter(audit_data=None, **kwargs):
    reporter = DependencyAuditReporter()
    if audit_data is not None:
        if isinstance(audit_data, dict):
            return reporter.generate_report(audit_data)
        return reporter.generate_report({"data": str(audit_data)})
    return reporter