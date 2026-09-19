import json
import os
import requests
from skills.incident_aggregator import aggregate_incidents
from skills.system_health_telemetry_collector import collect_telemetry


class SystemAuditLogExporter:
    """Модуль для экспорта системных логов аудита безопасности и инцидентов."""

    def export_log(self, target_url: str, raw_log_entry: dict) -> dict:
        try:
            response = requests.post(target_url, json=raw_log_entry)
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "event_id": data.get("event_id") or raw_log_entry.get("event_id")
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def export_stream(self, target_url: str, log_stream) -> dict:
        try:
            stream_content = log_stream.read()
            try:
                json_data = json.loads(stream_content.decode("utf-8") if isinstance(stream_content, bytes) else stream_content)
            except Exception:
                json_data = {"raw": str(stream_content)}

            response = requests.post(target_url, json=json_data)
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
        except Exception as e:
            try:
                response = requests.post(target_url)
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
            except Exception as inner_e:
                return {
                    "success": False,
                    "status_code": getattr(response, 'status_code', 500) if 'response' in locals() else 500,
                    "error": str(inner_e)
                }

    def format_standardized_logs(self, audit_records: list) -> str:
        payload = {"records": audit_records}
        return json.dumps(payload)


def export_system_audit_log(data: dict) -> dict:
    audit_id = data.get("audit_id", "default")
    incident = data.get("incident", {})
    output_directory = data.get("output_directory", ".")

    os.makedirs(output_directory, exist_ok=True)
    file_path = os.path.join(output_directory, f"audit_{audit_id}.json")

    export_data = {
        "audit_id": audit_id,
        "incident": incident
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    return {
        "exported_file": file_path
    }