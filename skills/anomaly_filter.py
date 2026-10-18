import os
from skills.anomaly_logger import AnomalyLogger

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

def start_new(data):
    if isinstance(data, list):
        results = []
        for item in data:
            if isinstance(item, dict):
                metric = item.get("metric", item.get("source", "unknown"))
                status = item.get("status", item.get("severity", "LOW"))
                if hasattr(status, "upper") and status.upper() in VALID_SEVERITIES:
                    sev = status.upper()
                elif status in ["critical", "warning"]:
                    sev = "CRITICAL" if status == "critical" else "HIGH"
                else:
                    sev = "LOW"
                val = item.get("value", "")
                details = f"Metric {metric} reached value {val}" if val != "" else item.get("details", "")
                results.append({
                    "source": f"sensor_{metric}",
                    "severity": sev,
                    "details": details,
                    "telemetry_snapshot": item,
                    "normalized": True
                })
        return results

    if isinstance(data, str):
        try:
            with open(data, 'r', encoding='utf-8') as f:
                content = f.read()
        except (OSError, FileNotFoundError, TypeError):
            content = data
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        content = content.strip()
        parts = content.split(":", 2)
        if len(parts) < 3:
            raise ValueError("Malformed stream data format")
        source, severity, details = parts[0], parts[1], parts[2]
        normalized = True
        if severity not in VALID_SEVERITIES:
            severity = "UNKNOWN"
            normalized = False
        return {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry_snapshot": {},
            "normalized": normalized
        }

    if not isinstance(data, dict):
        raise TypeError("Input must be a dict or file path string")

    if not all(k in data for k in ("source", "severity", "details", "telemetry_snapshot")):
        raise KeyError("Missing required keys in raw input data")

    severity = data["severity"]
    normalized = True
    if severity not in VALID_SEVERITIES:
        severity = "UNKNOWN"
        normalized = False

    return {
        "source": data["source"],
        "severity": severity,
        "details": data["details"],
        "telemetry_snapshot": data["telemetry_snapshot"],
        "normalized": normalized
    }

class AnomalyFilter:
    def __init__(self):
        pass

    def filter(self, raw_anomaly_data):
        if not isinstance(raw_anomaly_data, dict):
            raise TypeError("Input must be a dict")
        if not all(k in raw_anomaly_data for k in ("source", "severity", "details", "telemetry_snapshot")):
            raise KeyError("Missing required keys")
        
        severity = raw_anomaly_data["severity"]
        normalized = True
        if severity not in VALID_SEVERITIES:
            severity = "UNKNOWN"
            normalized = False

        return {
            "source": raw_anomaly_data["source"],
            "severity": severity,
            "details": raw_anomaly_data["details"],
            "telemetry_snapshot": raw_anomaly_data["telemetry_snapshot"],
            "normalized": normalized
        }