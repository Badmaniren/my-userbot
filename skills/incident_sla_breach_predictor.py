import io
import json

from skills import (
    incident_trend_analyzer,
    incident_sla_tracker,
    incident_trend_forecaster,
    incident_auto_escalation_engine
)

class IncidentSLABreachPredictor:
    def forecast_breach(self, incident_id):
        sla_data = incident_sla_tracker.get_tracking_data(incident_id)
        if sla_data is None:
            raise ValueError(f"Incident data not found for {incident_id}")
        
        trend_data = incident_trend_analyzer.analyze()
        
        risk_score = trend_data.get("risk_score", 0.0)
        time_remaining = sla_data.get("time_remaining_minutes", 1440)
        priority = sla_data.get("priority", "LOW")
        
        breach_predicted = False
        if risk_score > 0.5 or (priority in ["HIGH", "CRITICAL"] and time_remaining < 180):
            breach_predicted = True

        result = {
            "breach_predicted": breach_predicted,
            "incident_id": incident_id,
            "trend_reference": trend_data.get("trend_id")
        }
        return result

    def consume_forecaster_stream(self):
        return incident_trend_forecaster.stream_forecast()

    def force_escalate_prediction(self, incident_id):
        return incident_auto_escalation_engine.trigger_escalation(incident_id)


def incident_sla_breach_predictor(payload):
    incident_id = payload.get("incident_id")
    sla_data = payload.get("sla_data", {})
    trend_data = payload.get("trend_data", {})
    
    time_remaining = sla_data.get("sla_limit_seconds", 300) - sla_data.get("current_elapsed_seconds", 0)
    risk_score = trend_data.get("risk_factor", 0.0)
    
    breach_predicted = risk_score > 1.0 or time_remaining < 60
    
    return {
        "breach_predicted": bool(breach_predicted),
        "incident_id": incident_id,
        "trend_reference": trend_data.get("trend_id", "default_trend")
    }