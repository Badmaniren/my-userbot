"""
Automated Incident Triage and Smart Escalation Pipeline Skill Module
"""

from skills.incident_severity_evaluator import IncidentSeverityEvaluator, evaluate_incident_severity
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine, auto_escalate_incident
from skills.incident_triage_pipeline import IncidentTriagePipeline, triage_and_escalate_incident
from skills.incident_escalation_triage_bridge import IncidentEscalationTriageBridge, IncidentTriageEscalationBridge, bridge_triage_and_escalate


def automated_incident_triage_and_smart_esca(incident_payload):
    evaluator = IncidentSeverityEvaluator()
    engine = IncidentAutoEscalationEngine()
    pipeline = IncidentTriagePipeline()
    bridge = IncidentEscalationTriageBridge()

    if isinstance(incident_payload, dict):
        severity = evaluator.evaluate(incident_payload)
        decision = engine.determine_escalation(incident_payload, severity)
        triage_res = pipeline.run_pipeline(incident_payload)
        return bridge.bridge_triage_and_escalation(triage_res, decision)

    return bridge.process_bridge_triage_and_escalation(
        module_name="unknown",
        exception=Exception(str(incident_payload)),
        traceback_str="",
        incident_id="INC-AUTO",
        workspace_dir="/tmp"
    )


__all__ = [
    "IncidentSeverityEvaluator",
    "evaluate_incident_severity",
    "IncidentAutoEscalationEngine",
    "auto_escalate_incident",
    "IncidentTriagePipeline",
    "triage_and_escalate_incident",
    "IncidentEscalationTriageBridge",
    "IncidentTriageEscalationBridge",
    "bridge_triage_and_escalate",
    "automated_incident_triage_and_smart_esca",
]
