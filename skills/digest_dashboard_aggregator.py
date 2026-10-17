from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizer, AnomalyVisualizerError


class DigestDashboardAggregatorError(Exception):
    """Исключение для ошибок модуля DigestDashboardAggregator."""
    pass


class DigestDashboardAggregator:
    def __init__(self, stability_digest=None, anomaly_visualizer=None, digest_exporter=None):
        self.stability_digest = stability_digest
        self.anomaly_visualizer = anomaly_visualizer
        self.digest_exporter = digest_exporter

    def aggregate_operator_dashboard(self):
        try:
            metrics = self.anomaly_visualizer.get_summary_metrics()
            ascii_graph = self.anomaly_visualizer.render_ascii_correlation_graph()
            text_render = self.anomaly_visualizer.render_text()

            exporter = DigestExporter(
                stability_digest=self.stability_digest,
                anomaly_visualizer=self.anomaly_visualizer
            )
            exported_json = exporter.export_json_report()
            exported_html = exporter.export_html_report()

            return {
                "metrics": metrics,
                "ascii_graph": ascii_graph,
                "text_render": text_render,
                "exported_json": exported_json,
                "exported_html": exported_html
            }
        except (DigestExporterError, AnomalyVisualizerError) as e:
            raise DigestDashboardAggregatorError(str(e))
        except Exception as e:
            raise DigestDashboardAggregatorError(str(e))

    def export_stream_report(self, stream_id: str, output_path: str):
        try:
            exporter = DigestExporter(
                stability_digest=self.stability_digest,
                anomaly_visualizer=self.anomaly_visualizer
            )
            return exporter.export_stream_to_json(stream_id=stream_id, output_path=output_path)
        except Exception as e:
            raise DigestDashboardAggregatorError(str(e))

    def get_operator_summary_stream(self, data):
        return self.anomaly_visualizer.visualize_digest(data)

    def generate_operator_dashboard(self, output_path: str):
        try:
            exporter = self.digest_exporter if self.digest_exporter else DigestExporter(
                stability_digest=self.stability_digest,
                anomaly_visualizer=self.anomaly_visualizer
            )
            
            html_content = exporter.export_html_report(output_path=output_path)
            if not isinstance(html_content, str):
                html_content = str(html_content)
                
            if output_path:
                with open(output_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return content

            return output_path
        except Exception as e:
            raise DigestDashboardAggregatorError(str(e))