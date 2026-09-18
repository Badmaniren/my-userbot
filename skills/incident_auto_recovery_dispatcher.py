from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine
from skills.error_recovery_hub import ErrorRecoveryHub


class IncidentAutoRecoveryDispatcher:
    """
    Комбинирует движок автоэскалации инцидентов, хаб восстановления ошибок
    и SLA-координатор для завершения цикла автономного восстановления.
    """

    def __init__(self, escalation_engine=None, recovery_hub=None, sla_coordinator=None):
        self.escalation_engine = escalation_engine if escalation_engine is not None else IncidentAutoEscalationEngine()
        self.recovery_hub = recovery_hub if recovery_hub is not None else ErrorRecoveryHub()
        if sla_coordinator is not None:
            self.sla_coordinator = sla_coordinator
        else:
            from skills.incident_sla_recovery_coordinator import IncidentSlaRecoveryCoordinator
            self.sla_coordinator = IncidentSlaRecoveryCoordinator(recovery_dispatcher=self)

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
            if success:
                self.sla_coordinator.coordinate_sla_closure(incident_id)
            return bool(success)
        return False

    def evaluate_telemetry(self) -> dict:
        return self.escalation_engine.evaluate_system_telemetry_risks()

    def consume_and_process_stream(self) -> bytes:
        return self.escalation_engine.consume_stream_data()

    def dispatch_recovery(self, incident_id: str, module_name: str, exception: Exception) -> dict:
        context = {"incident_id": incident_id, "module_name": module_name}
        recovery_result = self.recovery_hub.analyze_and_recover(module_name, exception, context)
        escalation_result = self.escalation_engine.process_escalation(incident_id)
        sla_result = self.sla_coordinator.coordinate_sla_closure(incident_id)
        
        return {
            "incident_id": incident_id,
            "recovery_result": recovery_result,
            "escalation_result": escalation_result,
            "sla_coordination": sla_result,
            "status": "dispatched"
        }