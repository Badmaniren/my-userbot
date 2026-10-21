import json
from typing import Any, Dict, Optional, Union

from skills.anomaly_visualizer import AnomalyVisualizer
from skills.stability_digest import StabilityDigest


class DigestExporterError(Exception):
    """Исключение, выбрасываемое при ошибках экспорта дайджестов."""
    pass


class DigestExporter:
    """Модуль экспорта дайджестов и визуализаций в структурированные файлы отчетов."""

    def __init__(
        self,
        stability_digest: Optional[Union[StabilityDigest, Dict[str, Any]]] = None,
        anomaly_visualizer: Optional[AnomalyVisualizer] = None,
    ) -> None:
        self.digest: Optional[Union[StabilityDigest, Dict[str, Any]]] = stability_digest
        self.visualizer: Optional[AnomalyVisualizer] = anomaly_visualizer

    def export_json_report(self, output_path: str) -> str:
        """Экспортирует данные дайджеста и метрики визуализатора в JSON-файл."""
        try:
            if not self.visualizer:
                raise DigestExporterError("AnomalyVisualizer is not initialized")

            metrics = self.visualizer.get_summary_metrics()
            text_rep = self.visualizer.render_text()
            ascii_rep = self.visualizer.render_ascii_correlation_graph()

            if isinstance(metrics, dict):
                data = metrics.copy()
            else:
                data = {}

            data['text_report'] = text_rep
            data['ascii_graph'] = ascii_rep

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_html_report(self, output_path: str) -> str:
        """Экспортирует отчет в HTML-файл."""
        try:
            if not self.visualizer:
                raise DigestExporterError("AnomalyVisualizer is not initialized")

            metrics = self.visualizer.get_summary_metrics()
            text_rep = self.visualizer.render_text()
            ascii_rep = self.visualizer.render_ascii_correlation_graph()

            html_content = f"""<html>
    <head><title>Digest Report</title></head>
    <body>
        <h1>Stability Digest Report</h1>
        <div>Metrics: {metrics}</div>
        <div><pre>{text_rep}</pre></div>
        <div><pre>{ascii_rep}</pre></div>
    </body>
</html>"""

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_stream_to_json(self, stream_id: str, output_path: str) -> str:
        """Экспортирует поток дайджеста в JSON."""
        try:
            if self.digest is None:
                raise DigestExporterError("StabilityDigest is not initialized")

            if isinstance(self.digest, dict):
                stream_data = self.digest.get(stream_id, self.digest)
            elif hasattr(self.digest, "export_digest_stream"):
                stream_data = self.digest.export_digest_stream(stream_id)
            else:
                stream_data = {}

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stream_data, f, ensure_ascii=False, indent=4)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_to_json(self, output_path: str) -> str:
        """Метод-адаптер под интеграционный тест для экспорта в JSON."""
        try:
            if self.visualizer and hasattr(self.visualizer, 'digest') and isinstance(self.visualizer.digest, dict):
                data = self.visualizer.digest.copy()
            elif isinstance(self.digest, dict):
                data = self.digest.copy()
            elif self.digest and hasattr(self.digest, 'digest') and isinstance(self.digest.digest, dict):
                data = self.digest.digest.copy()
            else:
                data = {}

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_to_html(self, output_path: str) -> str:
        """Метод-адаптер под интеграционный тест для экспорта в HTML."""
        try:
            if self.visualizer and hasattr(self.visualizer, 'digest') and isinstance(self.visualizer.digest, dict):
                data = self.visualizer.digest
            elif isinstance(self.digest, dict):
                data = self.digest
            elif self.digest and hasattr(self.digest, 'digest') and isinstance(self.digest.digest, dict):
                data = self.digest.digest
            else:
                data = {}

            html_content = f"<html><body><pre>{json.dumps(data)}</pre></body></html>"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))