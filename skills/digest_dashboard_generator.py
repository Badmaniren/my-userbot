from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter


class DigestDashboardGeneratorError(Exception):
    """Кастомное исключение для генератора дашбордов дайджеста."""
    pass


class DigestDashboardGenerator:
    """
    Модуль для генерации итогового интерактивного дашборда 
    путем объединения возможностей визуализатора аномалий и экспортера дайджестов.
    Поддерживает как передачу готовых инстансов (для интеграционных тестов), 
    так и инициализацию «на лету» через словарь данных (для юнит-тестов).
    """

    def __init__(self, stability_digest=None, anomaly_visualizer=None, digest_exporter=None):
        self.digest_data = stability_digest

        if anomaly_visualizer is not None:
            self.visualizer = anomaly_visualizer
        else:
            self.visualizer = AnomalyVisualizer(digest=self.digest_data)

        if digest_exporter is not None:
            self.exporter = digest_exporter
        else:
            self.exporter = DigestExporter(stability_digest=self.digest_data, anomaly_visualizer=self.visualizer)

    def generate_dashboard(self, json_path: str, html_path: str) -> dict:
        try:
            json_res = self.exporter.export_to_json(json_path)
            html_res = self.exporter.export_to_html(html_path)
            return {
                'json_report': json_res,
                'html_report': html_res
            }
        except Exception as e:
            if isinstance(e, DigestDashboardGeneratorError):
                raise
            raise DigestDashboardGeneratorError(str(e))

    def get_metrics_summary(self) -> dict:
        return self.visualizer.get_summary_metrics()

    def render_ascii_graph(self) -> str:
        return self.visualizer.render_ascii_correlation_graph()

    def export_stream(self, stream_id: str, path: str) -> str:
        return self.exporter.export_stream_to_json(stream_id, path)

    def generate_html_dashboard(self, html_path: str) -> str:
        return self.exporter.export_to_html(html_path)

    def generate_json_dashboard(self, json_path: str) -> str:
        return self.exporter.export_to_json(json_path)