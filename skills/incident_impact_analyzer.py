import sys
import io
import json
import requests
from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub


class IncidentImpactAnalyzer:
    def __init__(self):
        pass

    def analyze_financial_impact(self, incident_id: str) -> dict:
        url = f"http://localhost/incidents/{incident_id}/metrics"
        try:
            response = requests.get(url)
            data = response.json()
        except Exception:
            data = {"downtime_minutes": 0, "cost_per_minute": 0.0}
            
        downtime_minutes = data.get("downtime_minutes", 0)
        cost_per_minute = data.get("cost_per_minute", 0.0)
        total_loss = downtime_minutes * cost_per_minute

        return {
            "incident_id": incident_id,
            "total_loss": total_loss,
            "downtime_minutes": downtime_minutes,
            "cost_per_minute": cost_per_minute
        }

    def analyze_operational_impact(self, incident_uuid: str) -> float:
        log_path = f"/var/log/incidents/{incident_uuid}.log"
        error_count = 0
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
                for line in content.splitlines():
                    if "ERROR" in line:
                        parts = line.split("count:")
                        if len(parts) > 1:
                            try:
                                error_count = float(parts[1].strip())
                            except ValueError:
                                error_count += 1
        except Exception:
            error_count = 100.0

        score = min(float(error_count) / 100.0, 100.0)
        return float(score)

    def aggregate_recovery_metrics(self) -> dict:
        aggregated = {}
        content = sys.stdin.read()
        for line in content.splitlines():
            if "METRIC" in line:
                parts = line.split("METRIC")
                if len(parts) > 1:
                    metric_str = parts[1].strip()
                    if "=" in metric_str:
                        key, val = metric_str.split("=", 1)
                        try:
                            aggregated[key.strip()] = int(val.strip())
                        except ValueError:
                            try:
                                aggregated[key.strip()] = float(val.strip())
                            except ValueError:
                                aggregated[key.strip()] = val.strip()
        return aggregated

    def calculate_severity_index(self, incident_token: str) -> float:
        fin = self.analyze_financial_impact(incident_token)
        financial_loss = fin.get("total_loss", 0.0)
        operational_degradation = self.analyze_operational_impact(incident_token)
        return float(financial_loss * operational_degradation)

    def analyze(self, data: dict) -> dict:
        incident = data.get("incident", {})
        incident_id = incident.get("incident_id", "")
        downtime = incident.get("downtime_minutes", 0)
        error_rate = incident.get("error_rate", 0.0)
        
        financial_loss = float(downtime * error_rate)
        operational_score = float(error_rate / 100.0)
        
        return {
            "incident_id": incident_id,
            "financial_loss": financial_loss,
            "operational_impact_score": operational_score
        }