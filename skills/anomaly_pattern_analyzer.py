import os
import json
import re


class AnomalyPatternAnalyzerError(Exception):
    """Кастомное исключение для ошибок модуля AnomalyPatternAnalyzer."""
    pass


class AnomalyPatternAnalyzer:
    """Модуль глубокого анализа текстовых и структурных паттернов аномалий."""

    def __init__(self, repo_path=None, log_path=None, threshold=0.5):
        self.repo_path = repo_path or "."
        self.log_path = log_path
        self.threshold = threshold

    def analyze_patterns(self, anomalies=None):
        """Анализирует паттерны аномалий и генерирует рекомендательный отчет."""
        if anomalies is None:
            if self.log_path and os.path.exists(self.log_path):
                logger = AnomalyLogger(self.log_path)
                anomalies = logger.get_anomalies()
            else:
                anomalies = []

        patterns = {}
        recommendations = []

        for item in anomalies:
            if isinstance(item, str):
                details_text = item
            elif isinstance(item, dict):
                details_text = str(item.get("details", ""))
            else:
                details_text = str(item)

            words = re.findall(r"\w+", details_text.lower())
            for w in words:
                if len(w) > 3:
                    patterns[w] = patterns.get(w, 0) + 1

        frequent_patterns = [k for k, v in patterns.items() if v >= 2]
        if frequent_patterns:
            recommendations.append(f"Обнаружены повторяющиеся слова-паттерны: {', '.join(frequent_patterns[:5])}")

        return {
            "total_analyzed": len(anomalies),
            "top_patterns": frequent_patterns,
            "recommendations": recommendations,
            "status": "success"
        }

    def extract_structural_patterns(self, telemetry_payload=None):
        """Извлекает структурные паттерны из нагрузок телеметрии."""
        if not isinstance(telemetry_payload, dict):
            return {"status": "error", "structural_signatures": []}

        signatures = list(telemetry_payload.keys())
        return {
            "status": "success",
            "structural_signatures": signatures
        }


class AnomalyFilter:
    def start_new(self, input_data):
        if not isinstance(input_data, dict) or not input_data:
            return {"status": "error", "filtered_data": {}}

        return {
            "filtered_data": input_data,
            "status": "processed"
        }


# Инициализируем локальный экземпляр без затенения импортов модулей
_anomaly_filter_instance = AnomalyFilter()


def __getattr__(name):
    if name == "anomaly_filter":
        return _anomaly_filter_instance
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


class AnomalyAuditHub:
    def __init__(self, repo_path: str, log_path: str, threshold: int):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.anomalies = []

    def log_anomaly(self, source: str, severity: str, details: str, telemetry_snapshot: dict):
        entry = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry_snapshot": telemetry_snapshot
        }
        self.anomalies.append(entry)

        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        data = []
        if os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    loaded = json.loads(content)
                    if isinstance(loaded, list):
                        data = [x if isinstance(x, dict) else {"details": str(x)} for x in loaded]
        data.append(entry)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def aggregate_and_report(self, metric_name: str, value: float):
        pass

    def generate_final_report(self):
        return {"report": "final", "status": "success"}


class AnomalyLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path

    def log_anomaly(self, source: str, severity: str, details: str, telemetry_snapshot: dict):
        entry = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry_snapshot": telemetry_snapshot
        }
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        data = []
        if os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    loaded = json.loads(content)
                    if isinstance(loaded, list):
                        data = [x if isinstance(x, dict) else {"details": str(x)} for x in loaded]
        data.append(entry)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def get_anomalies(self):
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content:
                return []
            loaded = json.loads(content)
            if isinstance(loaded, list):
                return [x if isinstance(x, dict) else {"details": str(x)} for x in loaded]
            return []

    def get_structured_report(self):
        return {"structured": True, "anomalies": self.get_anomalies()}
