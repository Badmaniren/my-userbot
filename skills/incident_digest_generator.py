from typing import Any, Dict, List, Optional
from skills.incident_aggregator import IncidentAggregator
from skills.notification_template_engine import NotificationTemplateEngine


class IncidentDigestGenerator:
    """
    Модуль для генерации периодических сводных дайджестов по инцидентам
    и результатам их автоматического устранения на основе агрегированных
    данных и шаблонов.
    """

    def __init__(self, aggregator: Optional[IncidentAggregator] = None, template_engine: Optional[NotificationTemplateEngine] = None):
        self.aggregator = aggregator if aggregator is not None else IncidentAggregator()
        self.template_engine = template_engine if template_engine is not None else NotificationTemplateEngine()

    def generate_digest(
        self,
        module_name: str,
        incidents: Optional[List[Dict[str, Any]]] = None,
        template_name: str = "incident_summary_template",
        format: str = "text"
    ) -> str:
        processed_incidents = []

        if incidents is not None and len(incidents) > 0:
            for incident in incidents:
                self.aggregator.process_and_aggregate(
                    module_name,
                    incident.get("exception"),
                    incident.get("traceback_str"),
                    incident.get("incident_id")
                )
            processed_incidents = incidents
        elif incidents is None:
            if hasattr(self.aggregator, "hub") and hasattr(self.aggregator.hub, "get_incident_history"):
                processed_incidents = self.aggregator.hub.get_incident_history(module_name)
            else:
                processed_incidents = []
        else:
            processed_incidents = []

        context: Dict[str, Any] = {
            "module_name": module_name,
            "incidents": processed_incidents,
        }

        if processed_incidents and isinstance(processed_incidents[-1], dict):
            last_inc = processed_incidents[-1]
            context["incident_id"] = last_inc.get("incident_id", "")
            context["error"] = last_inc.get("exception") or last_inc.get("error", "")

        return self.template_engine.render_template(
            template_name=template_name,
            context=context,
            format=format
        )

    def generate_and_export_digest(
        self,
        module_name: str,
        incidents: List[Dict[str, Any]],
        template_name: str,
        file_path: str,
        format: str = "text"
    ) -> bool:
        digest_content = self.generate_digest(
            module_name=module_name,
            incidents=incidents,
            template_name=template_name,
            format=format
        )
        context = {"digest_content": digest_content}
        return self.template_engine.export_notification_file(
            context=context,
            file_path=file_path
        )

    def export_digest(self, context: Dict[str, Any], file_path: str) -> bool:
        return self.template_engine.export_notification_file(context=context, file_path=file_path)

    def generate_digest_from_stream(
        self,
        stream: Any,
        template_name: str = "incident_summary_template",
        format: str = "html"
    ) -> str:
        parsed_payload = self.template_engine.parse_stream_data(stream) or {}
        module_name = parsed_payload.get("module_name", "")
        incidents = parsed_payload.get("incidents", [])

        return self.generate_digest(
            module_name=module_name,
            incidents=incidents,
            template_name=template_name,
            format=format
        )
