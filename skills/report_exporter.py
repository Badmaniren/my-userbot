import json
import os
from typing import Any, Dict


class ReportExporterError(Exception):
    """Исключение, возникающее при ошибках экспорта или валидации отчетов."""
    pass


class ReportExporter:
    """Класс для сериализации и экспорта отчетов аудита в JSON, текст и пользовательские форматы."""

    def __init__(self, data: Dict[str, Any]):
        if not isinstance(data, dict):
            raise ReportExporterError("Audit data must be a dictionary.")
        self.data = data
        self.report_id = data.get("report_id")

    def export_json(self) -> str:
        try:
            return json.dumps(self.data, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ReportExporterError(f"Failed to export to JSON: {e}")

    def export_json_to_file(self, file_path: str) -> None:
        try:
            content = self.export_json()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except ReportExporterError:
            raise
        except (OSError, IOError, PermissionError) as e:
            raise ReportExporterError(f"Failed to write JSON to file {file_path}: {e}")
        except Exception as e:
            raise ReportExporterError(f"Failed to write JSON to file {file_path}: {e}")

    def export_text(self) -> str:
        try:
            def _format_value(val: Any, indent_level: int = 0) -> str:
                ind = "  " * indent_level
                if isinstance(val, dict):
                    lines = []
                    for k, v in val.items():
                        lines.append(f"{ind}{k}:\n{_format_value(v, indent_level + 1)}")
                    return "\n".join(lines)
                elif isinstance(val, (list, tuple)):
                    lines = []
                    for item in val:
                        if isinstance(item, (dict, list, tuple)):
                            lines.append(f"{ind}-\n{_format_value(item, indent_level + 1)}")
                        else:
                            lines.append(f"{ind}- {item}")
                    return "\n".join(lines)
                else:
                    return f"{ind}{val}"

            lines = []
            for k, v in self.data.items():
                if isinstance(v, (dict, list, tuple)):
                    lines.append(f"{k}:\n{_format_value(v, 1)}")
                else:
                    lines.append(f"{k}: {v}")
            return "\n".join(lines)
        except Exception as e:
            raise ReportExporterError(f"Failed to export to text: {e}")

    def export_text_to_file(self, file_path: str) -> None:
        try:
            content = self.export_text()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except ReportExporterError:
            raise
        except (OSError, IOError, PermissionError) as e:
            raise ReportExporterError(f"Failed to write text to file {file_path}: {e}")
        except Exception as e:
            raise ReportExporterError(f"Failed to write text to file {file_path}: {e}")

    def export_custom_text(self, template: str) -> str:
        try:
            return template.format(**self.data)
        except KeyError as e:
            raise ReportExporterError(f"Missing key in template: {e}")
        except Exception as e:
            raise ReportExporterError(f"Failed to format custom text: {e}")

    def serialize(self) -> str:
        """Сериализует данные отчета в строку (используется в интеграционных тестах)."""
        return self.export_json()


def export_report(data: Dict[str, Any], file_path: str, format_type: str = "json") -> None:
    """Вспомогательная функция для экспорта отчета в файл по заданному формату."""
    exporter = ReportExporter(data)
    if not isinstance(format_type, str):
        raise ReportExporterError(f"Unsupported format type: {format_type}")

    fmt = format_type.lower()
    if fmt == "json":
        exporter.export_json_to_file(file_path)
    elif fmt == "text":
        exporter.export_text_to_file(file_path)
    else:
        raise ReportExporterError(f"Unsupported format type: {format_type}")