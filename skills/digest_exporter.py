import json


class DigestExporterError(Exception):
    """Исключение, выбрасываемое при ошибках экспорта дайджестов."""
    pass


class DigestExporter:
    """Модуль экспорта дайджестов и визуализаций в структурированные файлы отчетов."""

    def __init__(self, stability_digest=None, anomaly_visualizer=None):
        self.digest = stability_digest
        self.visualizer = anomaly_visualizer

    def validate_structure(self, data: dict) -> bool:
        """Валидирует структуру данных дайджеста."""
        return isinstance(data, dict)

    def export_json_report(self, output_path: str) -> str:
        """Экспортирует данные дайджеста и метрики визуализатора в JSON-файл."""
        try:
            metrics = self.visualizer.get_summary_metrics() if self.visualizer else {}
            text_rep = self.visualizer.render_text() if self.visualizer else ""
            ascii_rep = self.visualizer.render_ascii_correlation_graph() if self.visualizer else ""

            data = metrics.copy() if isinstance(metrics, dict) else {}
            data["text_report"] = text_rep
            data["ascii_graph"] = ascii_rep

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_html_report(self, output_path: str) -> str:
        """Экспортирует отчет в HTML-файл."""
        try:
            metrics = self.visualizer.get_summary_metrics() if self.visualizer else {}
            text_rep = self.visualizer.render_text() if self.visualizer else ""
            ascii_rep = self.visualizer.render_ascii_correlation_graph() if self.visualizer else ""

            html_content = f"""<html>
    <head><title>Digest Report</title></head>
    <body>
        <h1>Stability Digest Report</h1>
        <div>Metrics: {metrics}</div>
        <div><pre>{text_rep}</pre></div>
        <div><pre>{ascii_rep}</pre></div>
    </body>
</html>"""
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_markdown_report(self, output_path: str) -> str:
        """Экспортирует отчет в Markdown-файл."""
        try:
            metrics = self.visualizer.get_summary_metrics() if self.visualizer else {}
            text_rep = self.visualizer.render_text() if self.visualizer else ""
            ascii_rep = self.visualizer.render_ascii_correlation_graph() if self.visualizer else ""

            md_content = (
                f"# Stability Digest Report\n\n"
                f"## Metrics\n{metrics}\n\n"
                f"## Text Report\n```\n{text_rep}\n```\n\n"
                f"## Correlation Graph\n```\n{ascii_rep}\n```\n"
            )
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_stream_to_json(self, stream_id: str, output_path: str) -> str:
        """Экспортирует поток дайджеста в JSON."""
        try:
            if not self.digest:
                raise DigestExporterError("Digest object is missing")
            stream_data = self.digest.export_digest_stream(stream_id)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(stream_data, f, ensure_ascii=False, indent=4)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_to_json(self, output_path: str) -> str:
        """Метод-адаптер для экспорта в JSON."""
        try:
            data = (
                self.visualizer.digest
                if self.visualizer and hasattr(self.visualizer, "digest") and isinstance(self.visualizer.digest, dict)
                else {}
            )
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_to_html(self, output_path: str) -> str:
        """Метод-адаптер для экспорта в HTML."""
        try:
            data = (
                self.visualizer.digest
                if self.visualizer and hasattr(self.visualizer, "digest") and isinstance(self.visualizer.digest, dict)
                else {}
            )
            html_content = f"<html><body><pre>{json.dumps(data)}</pre></body></html>"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))

    def export_to_markdown(self, output_path: str) -> str:
        """Метод-адаптер для экспорта в Markdown."""
        try:
            data = (
                self.visualizer.digest
                if self.visualizer and hasattr(self.visualizer, "digest") and isinstance(self.visualizer.digest, dict)
                else {}
            )
            md_content = f"```json\n{json.dumps(data, ensure_ascii=False, indent=4)}\n```"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            return output_path
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e))