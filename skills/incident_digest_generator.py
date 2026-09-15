from skills.incident_aggregator import IncidentAggregator
from skills.notification_template_engine import NotificationTemplateEngine

class IncidentDigestGenerator:
    """
    Модуль для генерации периодических сводных дайджестов по инцидентам.
    Использует IncidentAggregator для обработки данных и NotificationTemplateEngine для рендеринга.
    """

    def __init__(self, aggregator=None, template_engine=None):
        self.aggregator = aggregator or IncidentAggregator()
        self.template_engine = template_engine or NotificationTemplateEngine()

    def generate_digest(self, module_name, incidents, template_name, format='text'):
        """Агрегирует инциденты и генерирует дайджест."""
        for incident in incidents:
            self.aggregator.process_and_aggregate(
                module_name=module_name,
                exception=incident.get("exception"),
                traceback_str=incident.get("traceback_str"),
                incident_id=incident.get("incident_id")
            )

        context = {
            "module_name": module_name,
            "incidents": incidents
        }

        return self.template_engine.render_template(
            template_name=template_name,
            context=context,
            format=format
        )

    def generate_and_export_digest(self, module_name, incidents, template_name, file_path, format='text'):
        """Генерирует дайджест и экспортирует его в файл."""
        digest_content = self.generate_digest(module_name, incidents, template_name, format)
        
        context = {
            "digest_content": digest_content
        }
        
        return self.template_engine.export_notification_file(
            context=context,
            file_path=file_path
        )

    def generate_digest_from_stream(self, stream, template_name, format='text'):
        """Парсит поток данных, агрегирует инциденты и генерирует дайджест."""
        payload = self.template_engine.parse_stream_data(stream)
        module_name = payload.get("module_name")
        incidents = payload.get("incidents", [])
        
        return self.generate_digest(module_name, incidents, template_name, format)

    def export_digest(self, context, file_path):
        """Прямой экспорт контекста в файл через шаблонизатор."""
        return self.template_engine.export_notification_file(
            context=context,
            file_path=file_path
        )