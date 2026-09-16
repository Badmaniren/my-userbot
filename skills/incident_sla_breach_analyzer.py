import io
from skills.incident_sla_tracker import IncidentSLATracker

# Создаем экземпляр трекера, ожидаемый тестами импорта
incident_sla_tracker = IncidentSLATracker()


class IncidentSLABreachAnalyzer:
    def analyze_breach_risk(self, historical_data, tracking_metrics):
        result = {}
        for inc in historical_data:
            inc_id = inc.get("id")
            metric = inc.get("metric")
            duration = inc.get("duration", 0.0)

            current_val = tracking_metrics.get(metric, 0.0) if isinstance(tracking_metrics, dict) else 0.0

            if not tracking_metrics or current_val == 0.0:
                risk_score = 0.0
            else:
                risk_score = float(current_val)

            is_imminent = current_val > duration if duration else False

            result[inc_id] = {
                "breach_risk_score": float(risk_score),
                "is_breach_imminent": is_imminent
            }
        return result

    def parse_and_analyze_stream(self, file_path):
        with open(file_path, "rb") as f:
            content = f.read().decode("utf-8")

        parsed_value = 0.0
        for part in content.split(","):
            if "value" in part:
                parsed_value = float(part.split(":")[1])

        return {
            "parsed_value": parsed_value
        }

    def analyze_with_tracker_dependency(self, historical_data, tracking_metrics):
        incident_sla_tracker.fetch_current_state()
        return self.analyze_breach_risk(historical_data, tracking_metrics)


def incident_sla_breach_analyzer(random_id, incident_data, tracking_metrics):
    analyzer = IncidentSLABreachAnalyzer()
    hist_data = [{
        "id": incident_data.get("id", random_id),
        "metric": incident_data.get("metric", "default"),
        "duration": float(incident_data.get("metric", 10)) if isinstance(incident_data.get("metric"), (int, float, str)) and str(incident_data.get("metric")).replace('.', '', 1).isdigit() else 10.0
    }]
    metrics = {incident_data.get("metric", "default"): tracking_metrics} if not isinstance(tracking_metrics, dict) else tracking_metrics

    analysis = analyzer.analyze_breach_risk(hist_data, metrics)
    risk_data = analysis.get(random_id, {"breach_risk_score": 0.0, "is_breach_imminent": False})

    return {
        "breach_risk": risk_data["breach_risk_score"],
        "incident_id": random_id
    }