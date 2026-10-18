from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator
import json
import os


class AnomalyAuditHub:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.log_path = log_path
        self.logger = AnomalyLogger(log_path=log_path)
        self.aggregator = AnomalyReportAggregator(
            repo_path=repo_path,
            log_path=log_path,
            threshold=threshold,
            logger=self.logger
        )

    def log_anomaly(self, source: str, severity: str, details: dict, telemetry_snapshot: dict):
        return self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def aggregate_and_report(self, metric_name: str, value: float):
        # Исправляем проблему с невалидными или строковыми логами (когда в лог-файле записаны простые строки вместо JSON),
        # переформатируя файл в валидные JSON-объекты или исправляя структуру перед вызовом агрегатора,
        # не нарушая при этом стандартные исключения там, где они ожидаются тестами.
        if self.log_path and os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                lines = content.splitlines()
                fixed_lines = []
                modified = False
                for line in lines:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        parsed = json.loads(line_str)
                        if isinstance(parsed, dict):
                            fixed_lines.append(line_str)
                        else:
                            # Если распарсился не словарь (например, строка или число), оборачиваем в словарь
                            fixed_lines.append(json.dumps({"source": "unknown", "details": {"message": parsed}}))
                            modified = True
                    except json.JSONDecodeError:
                        # Если строка не является валидным JSON, упаковываем её в словарь
                        fixed_lines.append(json.dumps({"source": "unknown", "details": {"message": line_str}}))
                        modified = True
                if modified:
                    with open(self.log_path, "w", encoding="utf-8") as f:
                        for fl in fixed_lines:
                            f.write(fl + "\n")

        return self.aggregator.aggregate_and_report(
            metric_name=metric_name,
            value=value
        )

    def generate_final_report(self):
        return self.aggregator.generate_final_report()