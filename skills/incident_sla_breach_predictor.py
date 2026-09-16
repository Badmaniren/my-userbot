import uuid
import io
import json
import os
from datetime import datetime

from skills.incident_aggregator import incident_aggregator
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_trend_analyzer import incident_trend_analyzer

class IncidentSLABreachPredictor:
    def __init__(self, historical_data=None):
        self.historical_data = historical_data or []

    def predict_breach(self, severity: str, response_time: float) -> dict:
        if not severity:
            raise ValueError("Severity cannot be empty")
        risk_score = response_time * (len(severity) / 10.0)
        will_breach = risk_score > 5.0
        return {
            "incident_id": uuid.uuid4().hex,
            "severity": severity,
            "response_time": response_time,
            "risk_score": risk_score,
            "will_breach": will_breach
        }

    def evaluate_stream(self, stream_io: io.BytesIO) -> list:
        content = stream_io.read().decode('utf-8')
        lines = content.splitlines()
        results = []
        for line in lines:
            parts = line.split(',')
            if len(parts) >= 2:
                sev = parts[0].strip()
                try:
                    rt = float(parts[1].strip())
                except ValueError:
                    rt = 1.0
                results.append(self.predict_breach(sev, rt))
        return results


def incident_sla_breach_predictor(payload: dict) -> dict:
    incident_id = payload.get("incident_id", uuid.uuid4().hex)
    severity = payload.get("severity", "LOW")
    response_time = float(payload.get("response_time_minutes", 10.0))

    risk_score = response_time * (len(severity) / 10.0)
    probability = min(max(risk_score / 20.0, 0.0), 1.0)
    breach_predicted = probability > 0.5

    result = {
        "incident_id": incident_id,
        "breach_predicted": breach_predicted,
        "probability": probability,
        "risk_score": risk_score
    }

    output_file_path = f"sla_prediction_{incident_id}.json"
    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(result, f)

    return result