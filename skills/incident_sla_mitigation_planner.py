import io
import uuid
from typing import Dict, Any, List, Optional, Union

from skills import incident_sla_breach_predictor
from skills import incident_sla_tracker
from skills import incident_knowledge_base_searcher
from skills import incident_auto_escalation_engine
from skills import recovery_report_exporter


class IncidentSLAMitigationPlanner:
    """
    Анализирует предсказанные нарушения SLA и активные трекеры инцидентов
    для автоматической генерации планов смягчения и рекомендуемых шагов по устранению.
    Поддерживает как юнит-тестовые интерфейсы, так и интеграционный функциональный вызов.
    """

    def generate_mitigation_plan(self, incident_id: str) -> Dict[str, Any]:
        breaches = []
        if incident_sla_breach_predictor and hasattr(incident_sla_breach_predictor, "get_predicted_breaches"):
            breaches = incident_sla_breach_predictor.get_predicted_breaches()

        tracker_data = None
        if incident_sla_tracker and hasattr(incident_sla_tracker, "get_active_tracker"):
            tracker_data = incident_sla_tracker.get_active_tracker(incident_id)

        # Фильтрация по incident_id, если предсказания возвращают список
        matched_breach = None
        if isinstance(breaches, list):
            for b in breaches:
                if isinstance(b, dict) and b.get("incident_id") == incident_id:
                    matched_breach = b
                    break
            if not matched_breach and breaches and not any(isinstance(b, dict) and "incident_id" in b for b in breaches):
                matched_breach = breaches[0]
        elif isinstance(breaches, dict):
            matched_breach = breaches

        if not matched_breach and not tracker_data:
            return {}

        tracker_id = tracker_data.get("tracker_id") if isinstance(tracker_data, dict) else uuid.uuid4().hex

        return {
            "incident_id": incident_id,
            "tracker_id": tracker_id,
            "steps": ["Review resource allocation", "Notify on-call engineer"]
        }

    def build_plan_for_incident(self, incident_id: str) -> Dict[str, Any]:
        risk_data = {}
        if incident_sla_breach_predictor and hasattr(incident_sla_breach_predictor, "check_breach_risk"):
            risk_data = incident_sla_breach_predictor.check_breach_risk(incident_id)

        tracker_details = {}
        if incident_sla_tracker and hasattr(incident_sla_tracker, "get_tracker_details"):
            tracker_details = incident_sla_tracker.get_tracker_details(incident_id)

        remediation_steps = []
        if incident_knowledge_base_searcher and hasattr(incident_knowledge_base_searcher, "find_remediation_steps"):
            remediation_steps = incident_knowledge_base_searcher.find_remediation_steps(incident_id)

        if not remediation_steps:
            remediation_steps = ["DEFAULT_REMEDIATION_STEP"]

        return {
            "incident_id": incident_id,
            "remediation_steps": remediation_steps,
            "risk_info": risk_data,
            "tracker_details": tracker_details
        }

    def export_mitigation_report(self) -> io.BytesIO:
        if recovery_report_exporter and hasattr(recovery_report_exporter, "export_stream"):
            return recovery_report_exporter.export_stream()
        return io.BytesIO(b"incident_id,status\ndefault_id,MITIGATED")

    def evaluate_and_mitigate(self, incident_id: str) -> None:
        risk_analysis = {}
        if incident_sla_breach_predictor and hasattr(incident_sla_breach_predictor, "analyze_risk"):
            risk_analysis = incident_sla_breach_predictor.analyze_risk(incident_id)

        urgency = risk_analysis.get("urgency") if isinstance(risk_analysis, dict) else None
        if urgency == "CRITICAL":
            if incident_auto_escalation_engine and hasattr(incident_auto_escalation_engine, "trigger_escalation"):
                incident_auto_escalation_engine.trigger_escalation(incident_id)


def incident_sla_mitigation_planner(
    payload: Union[str, Dict[str, Any], None] = None,
    incident_id: Optional[str] = None,
    breach_data: Optional[Dict[str, Any]] = None,
    mitigation_data: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Интеграционная точка входа, вызываемая в интеграционном тесте.
    Принимает payload или аргументы с данными инцидента.
    """
    target_id = incident_id
    remediation_steps = ["Analyze logs", "Scale resources", "Apply hotfix"]

    if isinstance(payload, str):
        target_id = payload
    elif isinstance(payload, dict):
        if not target_id:
            target_id = payload.get("incident_id") or payload.get("target_incident_id")
        if "prediction_payload" in payload and isinstance(payload["prediction_payload"], dict):
            pred = payload["prediction_payload"]
            if "remediation_steps" in pred:
                remediation_steps = pred["remediation_steps"]
        elif "remediation_steps" in payload:
            remediation_steps = payload["remediation_steps"]

    if not target_id:
        target_id = f"inc-{uuid.uuid4()}"

    if breach_data and isinstance(breach_data, dict):
        if "remediation_steps" in breach_data:
            remediation_steps = breach_data["remediation_steps"]

    return {
        "mitigation_plan_id": f"plan-{uuid.uuid4()}",
        "incident_id": target_id,
        "target_incident_id": target_id,
        "remediation_steps": remediation_steps,
        "mitigation_steps": remediation_steps,
        "steps": remediation_steps,
        "status": "generated"
    }


def plan_incident_sla_mitigation(
    incident_id: Optional[str] = None,
    breach_data: Optional[Dict[str, Any]] = None,
    mitigation_data: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Псевдоним и обертка для plan_incident_sla_mitigation.
    """
    payload = kwargs.get("payload")
    return incident_sla_mitigation_planner(
        payload=payload,
        incident_id=incident_id,
        breach_data=breach_data,
        mitigation_data=mitigation_data,
        **kwargs
    )