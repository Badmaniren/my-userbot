import os
from skills.anomaly_logger import AnomalyLogger

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

def start_new(data):
    if isinstance(data, str):
        with open(data, 'r', encoding='utf-8') as f:
            content = f.read()
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

    if isinstance(data, list):
        return [
            start_new(x) if isinstance(x, (dict, str)) else {
                "source": "raw_metric",
                "severity": "LOW",
                "details": str(x),
                "telemetry_snapshot": {"value": x},
                "normalized": True
            } for x in data
        ]

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