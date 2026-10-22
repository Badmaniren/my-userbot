import json
import os
from skills.anomaly_visualizer import AnomalyVisualizer


class DigestExporterError(Exception):
    """Исключение при ошибках экспорта дайджеста."""
    pass


class DigestExporter:
    """
    Класс экспорта дайджестов стабильности и отчетов визуализации
    в различные структурированные форматы (JSON, HTML, Markdown).
    """

    def __init__(self, stability_digest=None, anomaly_visualizer=None):
        self.stability_digest = stability_digest
        if anomaly_visualizer is not None:
            self.anomaly_visualizer = anomaly_visualizer
        else:
            # Если визуализатор не передан, создаем его на основе stability_digest,
            # учитывая, что stability_digest может быть словарем или объектом с атрибутом digest
            digest_data = None
            if isinstance(stability_digest, dict):
                digest_data = stability_digest
            elif hasattr(stability_digest, "digest") and isinstance(getattr(stability_digest, "digest"), dict):
                digest_data = getattr(stability_digest, "digest")

            try:
                self.anomaly_visualizer = AnomalyVisualizer(digest_data)
            except Exception:
                self.anomaly_visualizer = None

    def _get_metrics(self):
        """Вспомогательный метод получения метрик из visualizer или stability_digest."""
        if self.anomaly_visualizer is not None and hasattr(self.anomaly_visualizer, "get_summary_metrics"):
            try:
                metrics = self.anomaly_visualizer.get_summary_metrics()
                if metrics:
                    return metrics
            except Exception:
                pass

        if self.stability_digest is not None:
            if hasattr(self.stability_digest, "get_summary_metrics"):
                try:
                    metrics = self.stability_digest.get_summary_metrics()
                    if metrics:
                        return metrics
                except Exception:
                    pass
            if isinstance(self.stability_digest, dict):
                return self.stability_digest
            if hasattr(self.stability_digest, "digest") and isinstance(getattr(self.stability_digest, "digest"), dict):
                return getattr(self.stability_digest, "digest")

        return {}

    def _get_digest_dict(self):
        """Вспомогательный метод получения словаря дайджеста."""
        if self.stability_digest is not None:
            if isinstance(self.stability_digest, dict):
                return self.stability_digest
            if hasattr(self.stability_digest, "digest") and isinstance(getattr(self.stability_digest, "digest"), dict):
                return getattr(self.stability_digest, "digest")

        if self.anomaly_visualizer is not None and hasattr(self.anomaly_visualizer, "digest"):
            visualizer_digest = getattr(self.anomaly_visualizer, "digest")
            if isinstance(visualizer_digest, dict):
                return visualizer_digest

        return {}

    def export_json_report(self, output_path: str) -> str:
        """
        Экспортирует JSON отчет, содержащий сводные метрики,
        текстовый отчет и ASCII график корреляций.
        """
        try:
            metrics = self._get_metrics()
            text_report = ""
            ascii_graph = ""

            if self.anomaly_visualizer is not None:
                if hasattr(self.anomaly_visualizer, "render_text"):
                    text_report = self.anomaly_visualizer.render_text()
                if hasattr(self.anomaly_visualizer, "render_ascii_correlation_graph"):
                    ascii_graph = self.anomaly_visualizer.render_ascii_correlation_graph()

            report_data = dict(metrics)
            report_data["text_report"] = text_report
            report_data["ascii_graph"] = ascii_graph

            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise
            raise DigestExporterError(f"Ошибка при экспорте JSON отчета: {e}") from e

    def export_html_report(self, output_path: str) -> str:
        """
        Экспортирует HTML отчет с графическим представлением дайджеста.
        """
        try:
            metrics = self._get_metrics()
            digest_dict = self._get_digest_dict()

            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            html_lines = [
                "<html>",
                "<head><title>Digest Report</title></head>",
                "<body>",
                "<h1>Stability Digest Report</h1>",
                "<div class='metrics'>"
            ]

            combined_data = {**digest_dict, **metrics}
            for k, v in combined_data.items():
                html_lines.append(f"<p><strong>{k}</strong>: {v}</p>")

            html_lines.extend([
                "</div>",
                "</body>",
                "</html>"
            ])

            content = "\n".join(html_lines)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise
            raise DigestExporterError(f"Ошибка при экспорте HTML отчета: {e}") from e

    def export_markdown_report(self, output_path: str) -> str:
        """
        Экспортирует Markdown отчет на основе сведений о дайджесте.
        """
        try:
            metrics = self._get_metrics()
            digest_dict = self._get_digest_dict()

            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            md_lines = [
                "# Digest Report",
                "",
                "## Summary Metrics"
            ]

            combined_data = {**digest_dict, **metrics}
            for k, v in combined_data.items():
                md_lines.append(f"- **{k}**: {v}")

            content = "\n".join(md_lines)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise
            raise DigestExporterError(f"Ошибка при экспорте Markdown отчета: {e}") from e

    def export_stream_to_json(self, stream_id: str, output_path: str) -> str:
        """
        Экспортирует поток данных дайджеста по `stream_id` в JSON файл.
        """
        try:
            if self.stability_digest is None or not hasattr(self.stability_digest, "export_digest_stream"):
                raise DigestExporterError("stability_digest does not support export_digest_stream")

            stream_data = self.stability_digest.export_digest_stream(stream_id)

            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(stream_data, f, ensure_ascii=False, indent=2)

            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise
            raise DigestExporterError(f"Ошибка при экспорте потока в JSON: {e}") from e

    def export_to_json(self, output_path: str) -> str:
        """
        Адаптерный метод экспортa данных дайджеста в JSON файл.
        """
        try:
            digest_dict = self._get_digest_dict()

            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(digest_dict, f, ensure_ascii=False, indent=2)

            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise
            raise DigestExporterError(f"Ошибка при адаптивном экспорте в JSON: {e}") from e

    def export_to_html(self, output_path: str) -> str:
        """
        Адаптерный метод экспорта данных дайджеста в HTML файл.
        """
        try:
            digest_dict = self._get_digest_dict()

            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            html_content = f"<html><body><pre>{json.dumps(digest_dict)}</pre></body></html>"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise
            raise DigestExporterError(f"Ошибка при адаптивном экспорте в HTML: {e}") from e

    def export_to_markdown(self, output_path: str) -> str:
        """
        Адаптерный метод экспорта данных дайджеста в Markdown файл.
        """
        try:
            digest_dict = self._get_digest_dict()

            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            md_content = f"```json\n{json.dumps(digest_dict)}\n```"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise
            raise DigestExporterError(f"Ошибка при адаптивном экспорте в Markdown: {e}") from e
