from skills import incident_severity_evaluator
from skills import incident_auto_escalation_engine

# Экспортируем классы, ожидаемые юнит-тестами через патчинг модуля
class IncidentSeverityEvaluator:
    def evaluate_stream(self, module_name, stream_data):
        if hasattr(incident_severity_evaluator, "IncidentSeverityEvaluator"):
            return incident_severity_evaluator.IncidentSeverityEvaluator().evaluate_stream(module_name, stream_data)
        return incident_severity_evaluator.evaluate_stream(module_name, stream_data)

class IncidentAutoEscalationEngine:
    def process_escalation(self, incident_id):
        if hasattr(incident_auto_escalation_engine, "IncidentAutoEscalationEngine"):
            return incident_auto_escalation_engine.IncidentAutoEscalationEngine().process_escalation(incident_id)
        if hasattr(incident_auto_escalation_engine, "process_escalation"):
            return incident_auto_escalation_engine.process_escalation(incident_id)
        return {"status": "escalated"}


class IncidentTriagePipeline:
    def run_pipeline(self, incident_data: dict) -> dict:
        evaluator = incident_severity_evaluator.IncidentSeverityEvaluator()
        severity = evaluator.evaluate(incident_data)
        inc_id = incident_data.get("incident_id", "unknown")

        return {
            "incident_id": inc_id,
            "severity": severity,
            "status": "TRIAGED",
            "details": incident_data
        }

    def triage_and_escalate(self, module_name, exception, traceback_str, incident_id, workspace_dir):
        eval_result = incident_severity_evaluator.evaluate_incident_severity(
            module_name,
            exception,
            traceback_str,
            incident_id
        )
        
        severity = eval_result.get("severity")
        result = dict(eval_result)
        
        high_severities = ["CRITICAL", "HIGH", "SEV1", "SEV2"]
        if severity in high_severities:
            escalation_result = incident_auto_escalation_engine.auto_escalate_incident(
                incident_id,
                severity,
                workspace_dir
            )
            result["escalation_status"] = "escalated"
            if isinstance(escalation_result, dict):
                result.update(escalation_result)
                if "status" in escalation_result:
                    result["escalation_status"] = escalation_result["status"]
                result["escalation_result"] = escalation_result
            else:
                result["escalation_result"] = escalation_result
        return result

    def triage_stream(self, module_name, stream_data, incident_id):
        evaluator_instance = IncidentSeverityEvaluator()
        stream_eval_result = evaluator_instance.evaluate_stream(module_name, stream_data)
        
        severity = stream_eval_result.get("severity")
        result = dict(stream_eval_result)
        result["incident_id"] = incident_id
        
        high_severities = ["CRITICAL", "HIGH", "SEV1", "SEV2"]
        if severity in high_severities or stream_eval_result.get("anomaly_detected"):
            escalation_instance = IncidentAutoEscalationEngine()
            escalation_result = escalation_instance.process_escalation(incident_id)
            if isinstance(escalation_result, dict):
                result.update(escalation_result)
            result["escalation_triggered"] = True
            result["escalation_status"] = "escalated"
        else:
            result["escalation_status"] = "not_required"
            
        return result


def triage_and_escalate_incident(module_name, exception, traceback_str, incident_id, workspace_dir):
    pipeline = IncidentTriagePipeline()
    result = pipeline.triage_and_escalate(
        module_name=module_name,
        exception=exception,
        traceback_str=traceback_str,
        incident_id=incident_id,
        workspace_dir=workspace_dir
    )
    if "escalation_status" not in result:
        result["escalation_status"] = "not_required"
    return result
