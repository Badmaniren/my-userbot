from skills.anomaly_correlator import AnomalyCorrelator
from skills.system_telemetry import SystemTelemetry


class StabilityDigestError(Exception):
    """Исключение, возникающее при ошибках генерации или анализа дайджеста стабильности."""
    pass


class StabilityDigest:
    """Модуль для формирования аналитических дайджестов стабильности на основе телеметрии и аномалий."""

    def __init__(self, repo_path: str, anomaly_detector: AnomalyCorrelator, system_telemetry: SystemTelemetry):
        self.repo_path = repo_path
        self.anomaly_detector = anomaly_detector
        self.system_telemetry = system_telemetry

    def generate_digest(self, execution_id=None) -> dict:
        """Генерирует дайджест стабильности, объединяя сводку телеметрии и результаты детектирования аномалий."""
        try:
            summary = self.system_telemetry.get_telemetry_summary()
            anomalies = self.anomaly_detector.detect_anomalies()
            return {
                "summary": summary,
                "anomalies": anomalies
            }
        except Exception as e:
            if isinstance(e, StabilityDigestError):
                raise
            raise StabilityDigestError(str(e)) from e

    def export_digest_stream(self, stream_id: str) -> dict:
        """Экспортирует слепок телеметрии по заданному идентификатору потока."""
        return self.system_telemetry.collect_snapshot(stream_id)

    def analyze_digest_trends(self, metric_name: str) -> dict:
        """Анализирует тренды для указанной метрики на основе её истории."""
        try:
            history = self.system_telemetry.get_metric_history(metric_name)
            
            # Простейший расчет тренда
            trend = "stable"
            if len(history) > 1:
                if history[-1] > history[0]:
                    trend = "increasing"
                elif history[-1] < history[0]:
                    trend = "decreasing"

            return {
                "metric": metric_name,
                "history": history,
                "trend": trend
            }
        except Exception as e:
            if isinstance(e, StabilityDigestError):
                raise
            raise StabilityDigestError(str(e)) from e