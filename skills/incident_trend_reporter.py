import os
import requests
from typing import Dict, Any, Optional

from skills.incident_aggregator import incident_aggregator
from skills.incident_trend_analyzer import incident_trend_analyzer


class IncidentTrendReporter:
    def generate_report(self, filepath: str) -> Dict[str, Any]:
        trends = []
        errors = []
        total_incidents = 0

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            errors.append(str(e))
            return {"trends": [], "total_incidents": 0, "errors": errors}

        if isinstance(content, bytes):
            lines = content.decode('utf-8', errors='ignore').splitlines()
        elif isinstance(content, str):
            lines = content.splitlines()
        else:
            lines = []

        for line in lines:
            if isinstance(line, bytes):
                line = line.decode('utf-8', errors='ignore')
            line = line.strip()
            if not line:
                continue

            try:
                parts = {}
                for item in line.split(','):
                    if ':' in item:
                        key, val = item.split(':', 1)
                        parts[key.strip().lower()] = val.strip()

                if "id" in parts and "severity" in parts and "count" in parts:
                    item_id = parts["id"]
                    title = parts.get("title", "")
                    severity = parts["severity"]
                    count = int(parts["count"])

                    trends.append({
                        "id": item_id,
                        "title": title,
                        "severity": severity,
                        "count": count
                    })
                    total_incidents += count
                elif len(parts) >= 3 and len(line.split(',')) >= 3:
                    split_parts = line.split(',')
                    item_id = split_parts[0].strip()
                    severity = split_parts[1].strip()
                    count = int(split_parts[2].strip())

                    trends.append({
                        "id": item_id,
                        "title": "",
                        "severity": severity,
                        "count": count
                    })
                    total_incidents += count
                else:
                    errors.append(f"Malformed line: {line}")
            except Exception as e:
                errors.append(f"Error parsing line '{line}': {str(e)}")

        result: Dict[str, Any] = {
            "trends": trends,
            "total_incidents": total_incidents
        }
        if errors:
            result["errors"] = errors
        return result

    def aggregate_trends(self, filepath: str) -> Dict[str, Any]:
        parsed_entries = []
        try:
            with open(filepath, 'rb') as f:
                for raw_line in f:
                    if isinstance(raw_line, bytes):
                        line = raw_line.decode('utf-8', errors='ignore').strip()
                    else:
                        line = str(raw_line).strip()
                    if not line:
                        continue
                    parts = line.split(',')
                    if len(parts) >= 3:
                        try:
                            parsed_entries.append({
                                "id": parts[0].strip(),
                                "severity": parts[1].strip(),
                                "count": int(parts[2].strip())
                            })
                        except ValueError:
                            continue
        except Exception as e:
            return {
                "summary": "error",
                "total_entries": 0,
                "parsed_entries": [],
                "error": str(e)
            }

        return {
            "summary": "aggregated",
            "total_entries": len(parsed_entries),
            "parsed_entries": parsed_entries
        }

    def export_report(self, destination: str, payload: dict) -> dict:
        response = requests.post(destination, json=payload)
        return response.json()


incident_trend_reporter_instance = IncidentTrendReporter()


def incident_trend_reporter(analyzed_data: Optional[dict] = None, **kwargs) -> dict:
    os.makedirs("reports", exist_ok=True)
    payload = {}
    if isinstance(analyzed_data, dict):
        payload.update(analyzed_data)
    elif analyzed_data is not None:
        payload["data"] = analyzed_data
    payload.update(kwargs)

    inc_id = payload.get("analyzed_id") or payload.get("id") or payload.get("incident_id") or "UNKNOWN"
    file_path = f"reports/trend_report_{inc_id}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(payload))

    return {
        "report_id": inc_id,
        "file_path": file_path,
        "status": "generated"
    }
