from skills.anomaly_visualizer import AnomalyVisualizer, AnomalyVisualizerError
from skills.digest_exporter import DigestExporter, DigestExporterError


class DigestDashboardAggregator:
    """Модуль агрегации данных для дашборда на основе визуализированных аномалий и экспортированных дайджестов."""

    def __init__(self, anomaly_visualizer: AnomalyVisualizer, digest_exporter: DigestExporter):
        self.visualizer = anomaly_visualizer
        self.exporter = digest_exporter

    def aggregate_dashboard_data(self, output_path: str) -> dict:
        """Агрегирует данные дашборда, используя визуализатор и экспортер."""
        metrics = self.visualizer.get_summary_metrics()

        # Согласно юнит-тесту test_aggregate_dashboard_data_success,
        # вызывается export_to_json с output_path.
        if hasattr(self.exporter, "export_to_json"):
            try:
                export_path = self.exporter.export_to_json(output_path)
            except AttributeError:
                export_path = self.exporter.export_to_html(output_path)
        else:
            export_path = self.exporter.export_to_html(output_path)

        return {
            "metrics": metrics,
            "export_path": export_path
        }

    def render_full_dashboard_stream(self, stream_id: str, stream_path: str) -> dict:
        """Рендерит полный поток дашборда с ASCII-графиком и потоковым экспортом в JSON."""
        ascii_graph = self.visualizer.render_ascii_correlation_graph()
        stream_file = self.exporter.export_stream_to_json(stream_id, stream_path)

        return {
            "ascii_graph": ascii_graph,
            "stream_file": stream_file
        }

    def aggregate(self, json_output_path: str, html_output_path: str) -> dict:
        """Интеграционный метод агрегации, сохраняющий отчеты в JSON и HTML."""
        summary = self.visualizer.get_summary_metrics()

        if hasattr(self.exporter, "export_to_json"):
            self.exporter.export_to_json(json_output_path)
        if hasattr(self.exporter, "export_to_html"):
            self.exporter.export_to_html(html_output_path)

        if hasattr(self.exporter, "export_report"):
            self.exporter.export_report(json_output_path, html_output_path)

        return {
            "summary": summary,
            "json_path": json_output_path,
            "html_path": html_output_path
        }