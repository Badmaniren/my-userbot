import os
import json
import requests
from skills.vulnerability_scanner import scan_vulnerabilities

class IncidentSeverityEvaluator:
    def _external_check(self):
        return True

    def evaluate(self, telemetry: dict, vulnerabilities: list):
        self._external_check()

        has_critical_vuln = any(
            v.get("severity") == "CRITICAL" and v.get("exploit_available")
            for v in vulnerabilities
        )

        cvss = telemetry.get("cvss_score", 0.0)
        active_exploits = telemetry.get("active_exploits", False)

        if has_critical_vuln or (cvss >= 9.0 and active_exploits):
            severity = "CRITICAL"
        else:
            severity = "LOW"

        score = float(cvss if cvss > 0 else 2.5)

        return {
            "severity_level": severity,
            "score": score,
            "vulnerabilities": vulnerabilities,
            "telemetry": {k: str(v) if not isinstance(v, (int, float, bool, list, dict, type(None))) else v for k, v in telemetry.items()}
        }

    def calculate_risk_factor(self, telemetry_payload: dict) -> float:
        error_rate = telemetry_payload.get("error_rate", 0.0)
        unauthorized = telemetry_payload.get("unauthorized_access_attempts", 0)
        risk = (error_rate * 50.0) + (min(unauthorized, 500) / 10.0)
        return float(max(0.0, min(100.0, risk)))

    def evaluate_with_remote_telemetry(self, payload: dict) -> dict:
        endpoint = payload.get("endpoint")
        try:
            response = requests.get(endpoint, timeout=5)
            response.raise_for_status()
            return {"remote_verified": True}
        except Exception as e:
            return {"remote_verified": False, "error": str(e)}

def evaluate_incident_severity(incident_data: dict, output_path: str = None) -> dict:
    telemetry = incident_data.get("telemetry", {})
    vulnerabilities = incident_data.get("vulnerabilities", [])
    incident_id = incident_data.get("incident_id")

    evaluator = IncidentSeverityEvaluator()
    result = evaluator.evaluate(telemetry, vulnerabilities)

    report = {
        "incident_id": incident_id,
        "severity_level": result["severity_level"],
        "score": result["score"],
        "details": result
    }

    if output_path:
        os.makedirs(output_path, exist_ok=True)
        file_name = f"severity_{incident_id}.json"
        file_path = os.path.join(output_path, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=4)

    return report