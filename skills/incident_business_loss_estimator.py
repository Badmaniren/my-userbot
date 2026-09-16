import io
import json
from skills import incident_impact_analyzer


class IncidentBusinessLossEstimator:
    def calculate_financial_loss(self, impact_data: dict) -> dict:
        downtime = impact_data.get("downtime_minutes", 0)
        cost = impact_data.get("cost_per_minute", 0.0)
        total_loss = downtime * cost
        result = dict(impact_data)
        result["total_loss"] = total_loss
        return result

    def evaluate_operational_impact(self, incident_id: str) -> dict:
        if hasattr(incident_impact_analyzer, "get_metrics"):
            metrics = incident_impact_analyzer.get_metrics()
        elif hasattr(incident_impact_analyzer, "IncidentImpactAnalyzer"):
            analyzer = incident_impact_analyzer.IncidentImpactAnalyzer()
            metrics = analyzer.analyze({"incident_id": incident_id})
        elif callable(incident_impact_analyzer):
            metrics = incident_impact_analyzer({"incident_id": incident_id})
        else:
            metrics = {"component": "default", "severity": "MEDIUM", "loss_factor": 1.0}

        if not isinstance(metrics, dict):
            metrics = {"component": "default", "severity": "MEDIUM", "loss_factor": 1.0}

        severity_weights = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0, "CRITICAL": 5.0}
        sev = metrics.get("severity", "MEDIUM")
        loss_factor = metrics.get("loss_factor", 1.0)
        score = severity_weights.get(sev, 2.0) * loss_factor * 10.0

        return {
            "component": metrics.get("component"),
            "severity": sev,
            "loss_factor": loss_factor,
            "operational_score": score,
            "incident_id": incident_id
        }

    def export_loss_report_stream(self, report_data: dict) -> io.BytesIO:
        stream = io.BytesIO()
        content = json.dumps(report_data).encode("utf-8")
        stream.write(content)
        stream.seek(0)
        return stream

    def calculate_aggregate_losses(self, incidents: list) -> dict:
        total_aggregate_loss = 0.0
        for inc in incidents:
            total_aggregate_loss += inc.get("total_loss", 0.0)
        return {
            "total_aggregate_loss": total_aggregate_loss,
            "incident_count": len(incidents)
        }

    def parse_loss_from_stream(self, stream: io.BytesIO) -> dict:
        content = stream.read().decode("utf-8")
        return json.loads(content)


def incident_business_loss_estimator(data=None, **kwargs):
    if data is None and not kwargs:
        return IncidentBusinessLossEstimator()
    if data is None:
        data = kwargs
    if isinstance(data, dict):
        incident_id = data.get("incident_id")
        impact_data = data.get("impact_data", {})
        base_cost = data.get("base_cost_per_minute", 10.0)
        downtime = 0
        if isinstance(impact_data, dict):
            downtime = impact_data.get("downtime_minutes", 0)
        total_financial_loss = downtime * base_cost
        if total_financial_loss == 0.0:
            total_financial_loss = float(data.get("total_financial_loss", 100.0))
        return {
            "incident_id": incident_id,
            "total_financial_loss": total_financial_loss
        }
    return IncidentBusinessLossEstimator()
