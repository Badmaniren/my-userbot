import os
import json
import csv
import time
import pathlib
from typing import Dict, Any, Optional

from skills.repo_health_diagnostic import RepoHealthDiagnostic
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline


def start_new(
    health_data: Dict[str, Any],
    predictions: Dict[str, Any],
    export_format: str,
    output_path: Optional[str] = None
) -> str:
    """
    Экспортирует данные о здоровье репозитория и предсказания в выбранный формат (json, csv, markdown).
    """
    valid_formats = ["json", "csv", "markdown"]
    if export_format not in valid_formats:
        raise ValueError(f"Invalid export format: {export_format}. Must be one of {valid_formats}.")

    if not output_path:
        timestamp = int(time.time())
        output_path = f"repo_health_export_{timestamp}.{ 'md' if export_format == 'markdown' else export_format }"

    if export_format == "json":
        data = {
            "health": health_data,
            "predictions": predictions
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    elif export_format == "csv":
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Key", "Value"])
            for k, v in health_data.items():
                writer.writerow(["health", k, v])
            for k, v in predictions.items():
                writer.writerow(["predictions", k, v])

    elif export_format == "markdown":
        lines = ["# Repo Health & Predictions Export\n"]
        lines.append("## Health Data\n")
        for k, v in health_data.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("\n## Predictions\n")
        for k, v in predictions.items():
            lines.append(f"- **{k}**: {v}")
        
        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    return output_path


class RepoHealthExportHub:
    """
    Интеграционный класс-обертка для экспорта данных здоровья репозитория и предиктов.
    """
    def execute(
        self,
        diagnostic_data: Dict[str, Any],
        prediction_data: Dict[str, Any],
        export_format: str,
        target_directory: str
    ) -> Dict[str, Any]:
        valid_formats = ["json", "csv", "markdown"]
        if export_format not in valid_formats:
            raise ValueError(f"Unsupported format: {export_format}")

        ext = "md" if export_format == "markdown" else export_format
        filename = f"export_{int(time.time())}.{ext}"
        output_path = os.path.join(target_directory, filename)

        result_path = start_new(
            health_data=diagnostic_data,
            predictions=prediction_data,
            export_format=export_format,
            output_path=output_path
        )

        return {
            "status": "success",
            "file_path": result_path
        }