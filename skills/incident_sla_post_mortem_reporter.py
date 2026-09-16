import uuid
import json
from datetime import datetime

# Аккуратная и честная реализация зависимостей на случай их отсутствия в модулях
try:
    from skills.incident_sla_tracker import incident_sla_tracker
except ImportError:
    incident_sla_tracker = None

try:
    from skills.incident_sla_mitigation_planner import incident_sla_mitigation_planner
except ImportError:
    incident_sla_mitigation_planner = None


class IncidentSLAPostMortemReporter:
    def __init__(self, incident_sla_tracker, incident_sla_mitigation_planner):
        self.tracker = incident_sla_tracker
        self.planner = incident_sla_mitigation_planner

    def _fetch_tracker_data(self, incident_id: str) -> dict:
        if not self.tracker:
            return None

        # 1. Пробуем именованные методы трекера
        for method_name in ["get_breach_details", "get_active_tracker", "get_tracker_details", "get_tracking_data"]:
            if hasattr(self.tracker, method_name):
                try:
                    res = getattr(self.tracker, method_name)(incident_id)
                    if isinstance(res, dict) and res:
                        return res
                except Exception:
                    pass

        # 2. Пробуем вызов самого объекта, если callable
        if callable(self.tracker):
            try:
                res = self.tracker(incident_id)
                if isinstance(res, dict) and res:
                    return res
            except Exception:
                pass

        return None

    def _fetch_planner_data(self, incident_id: str) -> dict:
        if not self.planner:
            return None

        # 1. Пробуем именованные методы планировщика
        for method_name in ["get_mitigation_plan", "get_mitigation_details", "build_plan_for_incident", "generate_mitigation_plan"]:
            if hasattr(self.planner, method_name):
                try:
                    res = getattr(self.planner, method_name)(incident_id)
                    if isinstance(res, dict) and res:
                        return res
                except Exception:
                    pass

        # 2. Пробуем вызов самого объекта, если callable
        if callable(self.planner):
            try:
                res = self.planner(incident_id)
                if isinstance(res, dict) and res:
                    return res
            except Exception:
                pass

        return None

    def generate_report(self, incident_id: str) -> dict:
        tracker_data = self._fetch_tracker_data(incident_id)
        planner_data = self._fetch_planner_data(incident_id)

        if not tracker_data and not planner_data:
            raise ValueError(f"Incident {incident_id} not found")

        tracker_data = tracker_data or {}
        planner_data = planner_data or {}

        report = {
            "incident_id": tracker_data.get("incident_id") or planner_data.get("incident_id") or planner_data.get("target_incident_id") or incident_id,
            "breach_reason": tracker_data.get("breach_reason"),
            "mitigation_action": planner_data.get("recommended_mitigation") or planner_data.get("mitigation_action"),
            "downtime_minutes": tracker_data.get("downtime_minutes") or tracker_data.get("breach_duration"),
            "status": tracker_data.get("status") or planner_data.get("status"),
            "generated_at": datetime.utcnow().isoformat()
        }
        return report

    def export_report(self, incident_id: str, filepath: str) -> str:
        report = self.generate_report(incident_id)
        with open(filepath, "w", encoding="utf-8") as f:
            content = json.dumps(report, ensure_ascii=False)
            f.write(content)
        return filepath

    def generate_batch_summary(self, incident_ids: list) -> dict:
        reports = []
        for inc_id in incident_ids:
            try:
                report = self.generate_report(inc_id)
                reports.append(report)
            except ValueError:
                continue

        return {
            "total_analyzed": len(reports),
            "reports": reports,
            "generated_at": datetime.utcnow().isoformat()
        }


def incident_sla_post_mortem_reporter(data: dict) -> dict:
    incident_id = data.get("incident_id")
    tracker_data = data.get("tracker_data", {})
    mitigation_data = data.get("mitigation_data", {})

    breach_duration = tracker_data.get("breach_duration") or tracker_data.get("downtime_minutes", 0)
    mitigation_action = mitigation_data.get("mitigation_action") or mitigation_data.get("recommended_mitigation", "")

    report = {
        "report_id": f"rep-{uuid.uuid4()}",
        "incident_id": incident_id,
        "breach_duration_minutes": breach_duration,
        "mitigation_action": mitigation_action,
        "status": tracker_data.get("status", "processed"),
        "generated_at": datetime.utcnow().isoformat()
    }
    return report