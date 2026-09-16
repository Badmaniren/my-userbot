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
        if hasattr(incident_sla_tracker, "get_tracking_data"):
            sla_data = incident_sla_tracker.get_tracking_data(incident_id)
        elif callable(incident_sla_tracker):
            sla_data = incident_sla_tracker({"incident_id": incident_id})
        else:
            sla_data = None
            
        if sla_data is None:
            raise ValueError(f"Incident data not found for {incident_id}")
        
        if hasattr(incident_trend_analyzer, "analyze"):
            trend_data = incident_trend_analyzer.analyze()
        elif callable(incident_trend_analyzer):
            trend_data = incident_trend_analyzer({"incident_id": incident_id})
        else:
            trend_data = {}
        
        risk_score = trend_data.get("risk_score", trend_data.get("risk_factor", 0.0))
        time_remaining = sla_data.get("time_remaining_minutes", 1440)
        
        if "sla_limit_seconds" in sla_data and "current_elapsed_seconds" in sla_data:
            time_remaining = (sla_data.get("sla_limit_seconds", 300) - sla_data.get("current_elapsed_seconds", 0)) / 60.0

        priority = sla_data.get("priority", "LOW")
        status = sla_data.get("status", "")
        
        breach_predicted = False
        if status == "BREACHED" or risk_score > 0.5 or risk_score > 1.0 or (priority in ["HIGH", "CRITICAL"] and time_remaining < 180) or time_remaining < 1:
            breach_predicted = True

        result = {
            "breach_predicted": bool(breach_predicted),
            "incident_id": incident_id,
            "trend_reference": trend_data.get("trend_id", "default_trend")
        }
        return result

    def consume_forecaster_stream(self):
        return incident_trend_forecaster.stream_forecast()

    def force_escalate_prediction(self, incident_id):
        return incident_auto_escalation_engine.trigger_escalation(incident_id)


def incident_sla_breach_predictor(*args, **kwargs):
    if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], dict):
        incident_id, tracker_metrics = args[0], args[1]
        payload = {"incident_id": incident_id, "sla_data": tracker_metrics}
    elif len(args) == 1 and isinstance(args[0], dict):
        payload = args[0]
    elif len(args) == 1 and isinstance(args[0], str):
        payload = {"incident_id": args[0]}
    else:
        payload = kwargs

    incident_id = payload.get("incident_id")
    sla_data = payload.get("sla_data", {})
    trend_data = payload.get("trend_data", {})
    
    time_remaining = sla_data.get("sla_limit_seconds", 300) - sla_data.get("current_elapsed_seconds", 0)
    risk_score = trend_data.get("risk_factor", trend_data.get("risk_score", 0.0))
    status = sla_data.get("status", "")
    
    breach_predicted = status == "BREACHED" or risk_score > 1.0 or risk_score > 0.5 or time_remaining < 60
    
    return {
        "breach_predicted": bool(breach_predicted),
        "incident_id": incident_id,
        "trend_reference": trend_data.get("trend_id", "default_trend")
    }