from datetime import datetime
import json

class DependencyAuditReporter:
    def __init__(self):
        pass

    def generate_report(self, audit_data: dict) -> str:
        timestamp = datetime.now().isoformat()
        if "error_code" in audit_data:
            return f"ERROR: code {audit_data['error_code']} at {timestamp}"
        
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