import json
import os


class DigestExporterError(Exception):
    """Исключение, выбрасываемое при ошибках экспорта дайджестов."""
    pass


class DigestExporter:
    """Модуль экспорта дайджестов и визуализаций в структурированные файлы отчетов."""

    def __init__(self, stability_digest=None, anomaly_visualizer=None):
        self.digest = stability_digest
        self.visualizer = anomaly_visualizer

    def _ensure_dir(self, output_path: str):
        if output_path:
            dir_name = os.path.dirname(os.path.abspath(output_path))
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

    def _safe_execute(self, func, *args, **kwargs):
        """Внутренний хелпер для унификации обработки исключений."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, DigestExporterError):
                raise e
            raise DigestExporterError(str(e)) from e

    def _write_json(self, path: str, data):
        self._ensure_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return path

    def _write_text(self, path: str, content: str):
        self._ensure_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def export_json_report(self, output_path: str) -> str:
        """Экспортирует данные дайджеста и метрики визуализатора в JSON-файл."""
        def _logic():
            data = {}
            if self.visualizer:
                if hasattr(self.visualizer, 'get_summary_metrics'):
                    metrics = self.visualizer.get_summary_metrics()
                    if isinstance(metrics, dict):
                        data.update(metrics)
                elif isinstance(self.visualizer, dict):
                    data.update(self.visualizer)

                if hasattr(self.visualizer, 'render_text'):
                    data['text_report'] = self.visualizer.render_text()

                if hasattr(self.visualizer, 'render_ascii_correlation_graph'):
                    data['ascii_graph'] = self.visualizer.render_ascii_correlation_graph()
            elif self.digest:
                if hasattr(self.digest, 'generate_digest'):
                    digest_data = self.digest.generate_digest()
                    if isinstance(digest_data, dict):
                        data.update(digest_data)
                elif isinstance(self.digest, dict):
                    data.update(self.digest)

            return self._write_json(output_path, data)

        return self._safe_execute(_logic)

    def export_html_report(self, output_path: str) -> str:
        """Экспортирует отчет в HTML-файл."""
        def _logic():
            metrics = {}
            text_rep = ""
            ascii_rep = ""

            if self.visualizer:
                if hasattr(self.visualizer, 'get_summary_metrics'):
                    metrics = self.visualizer.get_summary_metrics()
                elif isinstance(self.visualizer, dict):
                    metrics = self.visualizer

                if hasattr(self.visualizer, 'render_text'):
                    text_rep = self.visualizer.render_text()

                if hasattr(self.visualizer, 'render_ascii_correlation_graph'):
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
            return self._write_text(output_path, html_content)

        return self._safe_execute(_logic)

    def export_markdown_report(self, output_path: str) -> str:
        """Экспортирует отчет в Markdown-файл."""
        def _logic():
            metrics = {}
            text_rep = ""
            ascii_rep = ""

            if self.visualizer:
                if hasattr(self.visualizer, 'get_summary_metrics'):
                    metrics = self.visualizer.get_summary_metrics()
                elif isinstance(self.visualizer, dict):
                    metrics = self.visualizer

                if hasattr(self.visualizer, 'render_text'):
                    text_rep = self.visualizer.render_text()

                if hasattr(self.visualizer, 'render_ascii_correlation_graph'):
                    ascii_rep = self.visualizer.render_ascii_correlation_graph()

            md_content = f"""# Stability Digest Report

## Summary Metrics
```json
{json.dumps(metrics, ensure_ascii=False, indent=2) if isinstance(metrics, dict) else str(metrics)}
```

## Text Report
```
{text_rep}
```

## Correlation Graph
```
{ascii_rep}
```
"""
            return self._write_text(output_path, md_content)

        return self._safe_execute(_logic)

    def export_stream_to_json(self, stream_id: str, output_path: str) -> str:
        """Экспортирует поток дайджеста в JSON."""
        def _logic():
            if self.digest and hasattr(self.digest, 'export_digest_stream'):
                stream_data = self.digest.export_digest_stream(stream_id)
            elif isinstance(self.digest, dict):
                stream_data = self.digest.get(stream_id, {})
            else:
                stream_data = {}
            return self._write_json(output_path, stream_data)

        return self._safe_execute(_logic)

    def export_to_json(self, output_path: str) -> str:
        """Метод-адаптер под интеграционный тест для экспорта в JSON."""
        def _logic():
            data = {}
            if self.visualizer and hasattr(self.visualizer, 'digest') and isinstance(self.visualizer.digest, dict):
                data = self.visualizer.digest.copy()
            elif isinstance(self.digest, dict):
                data = self.digest.copy()
            elif self.digest and hasattr(self.digest, 'generate_digest'):
                digest_res = self.digest.generate_digest()
                if isinstance(digest_res, dict):
                    data = digest_res
            return self._write_json(output_path, data)

        return self._safe_execute(_logic)

    def export_to_html(self, output_path: str) -> str:
        """Метод-адаптер под интеграционный тест для экспорта в HTML."""
        def _logic():
            data = {}
            if self.visualizer and hasattr(self.visualizer, 'digest') and isinstance(self.visualizer.digest, dict):
                data = self.visualizer.digest
            elif isinstance(self.digest, dict):
                data = self.digest
            html_content = f"<html><body><pre>{json.dumps(data, ensure_ascii=False)}</pre></body></html>"
            return self._write_text(output_path, html_content)

        return self._safe_execute(_logic)

    def export_to_markdown(self, output_path: str) -> str:
        """Метод-адаптер под интеграционный тест для экспорта в Markdown."""
        def _logic():
            data = {}
            if self.visualizer and hasattr(self.visualizer, 'digest') and isinstance(self.visualizer.digest, dict):
                data = self.visualizer.digest
            elif isinstance(self.digest, dict):
                data = self.digest
            md_content = f"# Digest Data\n\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
            return self._write_text(output_path, md_content)

        return self._safe_execute(_logic)
