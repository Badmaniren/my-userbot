from skills.incident_triage_pipeline import IncidentTriagePipeline
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine


class IncidentEscalationTriageBridge:
    def __init__(self):
        self.triage_pipeline = IncidentTriagePipeline()
        self.escalation_engine = IncidentAutoEscalationEngine()

    def process_bridge_triage_and_escalation(self, module_name, exception, traceback_str, incident_id, workspace_dir):
        triage_res = self.triage_pipeline.triage_and_escalate(module_name, exception, traceback_str, incident_id, workspace_dir)
        escalation_res = self.escalation_engine.process_escalation(incident_id)
        return {
            "triage": triage_res,
            "escalation": escalation_res
        }


class IncidentTriageEscalationBridge:
    def __init__(self):
        self.triage_pipeline = IncidentTriagePipeline()
        self.escalation_engine = IncidentAutoEscalationEngine()

    def process_end_to_end(self, module_name, exception, traceback_str, incident_id, workspace_dir):
        triage_res = self.triage_pipeline.triage_and_escalate(module_name, exception, traceback_str, incident_id, workspace_dir)
        escalation_res = self.escalation_engine.process_escalation(incident_id)
        
        result = {}
        if isinstance(triage_res, dict):
            result.update(triage_res)
        if isinstance(escalation_res, dict):
            result.update(escalation_res)
            
        result["incident_id"] = incident_id
        if "escalation_status" not in result:
            result["escalation_status"] = "processed"
            
        return result


def bridge_triage_and_escalate(module_name, exception, traceback_str, incident_id, workspace_dir):
    bridge = IncidentTriageEscalationBridge()
    return bridge.process_end_to_end(module_name, exception, traceback_str, incident_id, workspace_dir)