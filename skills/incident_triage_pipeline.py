from skills import incident_severity_evaluator
from skills import incident_auto_escalation_engine

class IncidentTriagePipeline:
    def triage_and_escalate(self, module_name, exception, traceback_str, incident_id, workspace_dir):
        eval_result = incident_severity_evaluator.evaluate_incident_severity(
            module_name,
            exception,
            traceback_str,
            incident_id
        )
        
        severity = eval_result.get("severity")
        result = dict(eval_result)
        
        # Determine if escalation is needed based on severity
        # Supports CRITICAL, HIGH, and integration test severities like SEV1, SEV2
        high_severities = ["CRITICAL", "HIGH", "SEV1", "SEV2"]
        if severity in high_severities:
            escalation_result = incident_auto_escalation_engine.auto_escalate_incident(
                incident_id,
                severity,
                workspace_dir
            )
            if isinstance(escalation_result, dict):
                result.update(escalation_result)
                if "status" in escalation_result:
                    result["escalation_status"] = escalation_result["status"]
                else:
                    result["escalation_status"] = "escalated"
                result["escalation_result"] = escalation_result
            else:
                result["escalation_status"] = "escalated"
                result["escalation_result"] = escalation_result
                
        return result

    def triage_stream(self, module_name, stream_data, incident_id):
        evaluator_instance = incident_severity_evaluator.IncidentSeverityEvaluator()
        stream_eval_result = evaluator_instance.evaluate_stream(module_name, stream_data)
        
        severity = stream_eval_result.get("severity")
        result = dict(stream_eval_result)
        result["incident_id"] = incident_id
        
        high_severities = ["CRITICAL", "HIGH", "SEV1", "SEV2"]
        if severity in high_severities or stream_eval_result.get("anomaly_detected"):
            escalation_instance = incident_auto_escalation_engine.IncidentAutoEscalationEngine()
            escalation_result = escalation_instance.process_escalation(incident_id)
            if isinstance(escalation_result, dict):
                result.update(escalation_result)
            result["escalation_triggered"] = True
            
        return result


def triage_and_escalate_incident(module_name, exception, traceback_str, incident_id, workspace_dir):
    pipeline = IncidentTriagePipeline()
    return pipeline.triage_and_escalate(
        module_name=module_name,
        exception=exception,
        traceback_str=traceback_str,
        incident_id=incident_id,
        workspace_dir=workspace_dir
    )