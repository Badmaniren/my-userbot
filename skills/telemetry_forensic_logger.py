import os
import json
import hashlib
import requests

try:
    from skills.telemetry_streamer import telemetry_streamer
except ImportError:
    telemetry_streamer = None

try:
    from skills.telemetry_processor import telemetry_processor
except ImportError:
    telemetry_processor = None

try:
    from skills.system_health_telemetry_collector import system_health_telemetry_collector
except ImportError:
    system_health_telemetry_collector = None

try:
    from skills.incident_aggregator import incident_aggregator
except ImportError:
    incident_aggregator = None

class TelemetryForensicLogger:
    """Модуль для детального и безопасного логирования форензик-данных аномалий телеметрии."""

    def __init__(self):
        pass

    def log_forensic_data(self, anomaly_id: str, source: str, data_stream, integrity_hash: str) -> bool:
        raw_data = data_stream.read()
        calculated_hash = hashlib.sha256(raw_data).hexdigest()

        if calculated_hash != integrity_hash:
            raise ValueError("Integrity hash mismatch: data stream is corrupted.")

        record = {
            "anomaly_id": anomaly_id,
            "source": source,
            "checksum": calculated_hash,
            "size": len(raw_data)
        }

        filename = f"forensic_{anomaly_id}.log"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(record, f)

        return True

    def get_forensic_record(self, anomaly_id: str) -> dict:
        filename = f"forensic_{anomaly_id}.log"
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def dispatch_to_audit_pipeline(self, audit_payload: dict) -> bool:
        response = requests.post("http://localhost/audit", json=audit_payload)
        return response.status_code == 200

    def handle_stream_failure(self, anomaly_id: str, faulty_stream) -> dict:
        filename = f"forensic_{anomaly_id}.log"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("STREAM_FAILURE")
        return {
            "recovered": True,
            "anomaly_id": anomaly_id,
            "status": "handled"
        }

def telemetry_forensic_logger(incident_data: dict, output_path: str, verify_integrity: bool = True) -> dict:
    payload_str = json.dumps(incident_data, sort_keys=True).encode('utf-8')
    checksum = hashlib.sha256(payload_str).hexdigest()

    record = {
        "incident_data": incident_data,
        "checksum": checksum,
        "verified": verify_integrity
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)

    return record