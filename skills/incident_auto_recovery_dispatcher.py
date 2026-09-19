from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine
from skills.error_recovery_hub import ErrorRecoveryHub


class IncidentAutoRecoveryDispatcher:
    """
    Комбинирует движок автоэскалации инцидентов и хаб восстановления ошибок 
    для автоматического запуска процедур ликвидации сбоев.
    """

    def dispatch(self, incident_context: dict, mitigation_plan: dict = None) -> dict:
        if isinstance(incident_context, str):
            incident_id = incident_context
        elif isinstance(incident_context, dict):
            incident_id = incident_context.get("incident_id", "INC-UNKNOWN")
        else:
            incident_id = "INC-UNKNOWN"

        escalation_result = self.dispatch_escalation(incident_id)

        return {
            "incident_id": incident_id,
            "status": "DISPATCHED",
            "recovery_triggered": True,
            "escalation_result": escalation_result,
            "mitigation_plan": mitigation_plan
        }

    def __init__(self):
        self.escalation_engine = IncidentAutoEscalationEngine()
        self.recovery_hub = ErrorRecoveryHub()

    def dispatch_escalation(self, incident_id: str):
        return self.escalation_engine.process_escalation(incident_id)

    def handle_runtime_failure(self, module_name: str, exception: Exception, context: dict):
        return self.recovery_hub.analyze_and_recover(module_name, exception, context)

    def run_full_recovery_cycle(self, module_name: str, exception: Exception, traceback_str: str) -> bool:
        incident_id = self.recovery_hub.capture_failure(module_name, exception, traceback_str)
        if isinstance(incident_id, dict):
            incident_id = incident_id.get("incident_id", str(incident_id))
        
        should_patch = self.escalation_engine.check_and_trigger_patching()
        if should_patch:
            patch_payload = self.recovery_hub.generate_patch(incident_id)
            success = self.recovery_hub.deploy_and_verify(incident_id, patch_payload)
            return bool(success)
        return False

    def evaluate_telemetry(self) -> dict:
        return self.escalation_engine.evaluate_system_telemetry_risks()

    def consume_and_process_stream(self) -> bytes:
        data = self.escalation_engine.consume_stream_data()
        if isinstance(data, str):
            return data.encode('utf-8')
        if isinstance(data, bytes):
            return data
        if isinstance(data, (list, tuple)):
            return bytes(data)
        return b""

    def dispatch_recovery(self, incident_id: str, module_name: str, exception: Exception) -> dict:
        context = {"incident_id": incident_id, "module_name": module_name}
        recovery_result = self.recovery_hub.analyze_and_recover(module_name, exception, context)
        escalation_result = self.escalation_engine.process_escalation(incident_id)
        
        return {
            "incident_id": incident_id,
            "recovery_result": recovery_result,
            "escalation_result": escalation_result,
            "status": "dispatched"
        }