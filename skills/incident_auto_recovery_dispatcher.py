from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_audit_trail_collector import IncidentAuditTrailCollector
from skills.system_health_aggregator import SystemHealthAggregator


class IncidentAutoRecoveryDispatcher:
    """
    Комбинирует движок автоэскалации инцидентов и хаб восстановления ошибок 
    для автоматического запуска процедур ликвидации сбоев с интеграцией аудита и проверки здоровья.
    """

    def __init__(self):
        self.escalation_engine = IncidentAutoEscalationEngine()
        self.recovery_hub = ErrorRecoveryHub()
        self.audit_collector = IncidentAuditTrailCollector()
        self.health_aggregator = SystemHealthAggregator()

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

            if hasattr(self.audit_collector, "record_audit_event"):
                self.audit_collector.record_audit_event({
                    "incident_id": incident_id,
                    "module_name": module_name,
                    "status": "patched" if success else "failed"
                })
            if hasattr(self.health_aggregator, "verify_system_stability"):
                self.health_aggregator.verify_system_stability()

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
        
        if hasattr(self.audit_collector, "record_audit_event"):
            self.audit_collector.record_audit_event({
                "incident_id": incident_id,
                "module_name": module_name,
                "status": "dispatched"
            })

        return {
            "incident_id": incident_id,
            "recovery_result": recovery_result,
            "escalation_result": escalation_result,
            "status": "dispatched"
        }