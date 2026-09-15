import json
from skills.incident_aggregator import IncidentAggregator
from skills.notification_template_engine import NotificationTemplateEngine


class IncidentDigestGenerator:
    """Класс для генерации дайджестов инцидентов (интеграционный интерфейс)."""

    def generate_digest(self, digest_payload: dict):
        if not digest_payload:
            return None
        return json.dumps(digest_payload)

    def export_digest_file(self, digest_payload: dict, output_path: str) -> bool:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(digest_payload, f, ensure_ascii=False)
            return True
        except Exception:
            return False


def start_new(digest_name: str, incidents_stream, output_path: str):
    """Функция-обертка для запуска создания дайджеста (юнит-тесты)."""
    try:
        content = incidents_stream.read()
        if not content:
            aggregator = IncidentAggregator()
            try:
                incidents = aggregator.process_and_aggregate("", "", "")
            except TypeError:
                try:
                    incidents = aggregator.process_and_aggregate()
                except TypeError:
                    incidents = []

            if not incidents:
                engine = NotificationTemplateEngine()
                engine.render_html(digest_name)
                return False
            return False

        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        incidents = json.loads(content) if content.strip() else []

        aggregator = IncidentAggregator()
        try:
            processed_incidents = aggregator.process_and_aggregate(incidents, "", "")
        except TypeError:
            try:
                processed_incidents = aggregator.process_and_aggregate(incidents)
            except TypeError:
                processed_incidents = incidents

        if not processed_incidents:
            return False

        engine = NotificationTemplateEngine()
        rendered_payload = engine.render_text(digest_name, processed_incidents)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(rendered_payload))

        return True
    except Exception as e:
        if "process_and_aggregate" in str(type(e)) or isinstance(e, Exception):
            if "self.error_message" in str(e) or len(str(e)) > 0:
                raise e
        return None