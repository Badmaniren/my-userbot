from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter


class DigestDashboardBuilderError(Exception):
    """Кастомное исключение для ошибок построения дашборда дайджестов."""
    pass


class DigestDashboardBuilder:
    """
    Класс для сборки дашборда на основе визуализированных данных и экспортированных дайджестов.
    Поддерживает инициализацию как по сырым данным, так и через готовые компоненты (для интеграционных тестов).
    """

    def __init__(self, digest_data=None, anomaly_visualizer=None, digest_exporter=None):
        if anomaly_visualizer is not None:
            self.visualizer = anomaly_visualizer
        else:
            self.visualizer = AnomalyVisualizer(digest_data)

        if digest_exporter is not None:
            self.exporter = digest_exporter
        else:
            self.exporter = DigestExporter(
                stability_digest=digest_data,
                anomaly_visualizer=self.visualizer
            )

    def build_dashboard(self, json_output_path=None, html_output_path=None):
        try:
            rendered_text = self.visualizer.render_text()
            correlation_graph = self.visualizer.render_ascii_correlation_graph()
            summary_metrics = self.visualizer.get_summary_metrics()

            json_path = None
            html_path = None

            if json_output_path:
                json_path = self.exporter.export_to_json(json_output_path)
            if html_output_path:
                html_path = self.exporter.export_to_html(html_output_path)

            # Поддерживаем структуру ключей как для юнит-, так и для интеграционных тестов
            dashboard = {
                "text_report": rendered_text,
                "correlation_graph": correlation_graph,
                "summary_metrics": summary_metrics,
                "json_export_path": json_path,
                "html_export_path": html_path,
                "summary": summary_metrics,
                "reports": {
                    "text_report": rendered_text,
                    "correlation_graph": correlation_graph
                }
            }
            return dashboard
        except Exception as e:
            if isinstance(e, DigestDashboardBuilderError):
                raise
            raise DigestDashboardBuilderError(str(e)) from e