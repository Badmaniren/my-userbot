import uuid
import os
import json
from skills.incident_sla_tracker import IncidentSlaTracker
from skills.incident_sla_breach_predictor import IncidentSlaBreachPredictor
from skills.incident_aggregator import IncidentAggregator

class IncidentSLAViolationAnalyzer:
    def __init__(self):
        pass

    def analyze_root_causes(self, incident_data=None, prediction_metrics=None, incident_id=None):
        if not incident_data:
            raise ValueError("Incident data cannot be empty")

        analysis_id = uuid.uuid4().hex
        cause = incident_data.get("cause", "unknown")
        score = prediction_metrics.get("score", 0.0 if prediction_metrics else 0.5) if prediction_metrics else 0.5

        target_incident_id = incident_id or incident_data.get("incident_id", incident_data.get("id", analysis_id))

        report = {
            "analysis_id": analysis_id,
            "root_cause": cause,
            "root_causes": [cause],
            "prediction_score": score,
            "actionable_insights": ["Optimize resource allocation", "Update SLA thresholds"],
            "analyzed_incident_id": target_incident_id
        }

        report_file_path = f"sla_analysis_{target_incident_id}.json"
        with open(report_file_path, "w") as f:
            json.dump(report, f)

        return report

IncidentSlaviolationAnalyzer = IncidentSLAViolationAnalyzer
incident_sla_violation_analyzer = IncidentSLAViolationAnalyzer