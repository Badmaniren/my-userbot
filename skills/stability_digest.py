from skills.anomaly_correlator import AnomalyCorrelator
from skills.system_telemetry import SystemTelemetry


class StabilityDigestError(Exception):
    """Исключение, возникающее при ошибках генерации или анализа дайджеста стабильности."""
    pass


class StabilityDigest:
    """Модуль для формирования аналитических дайджестов стабильности на основе телеметрии и аномалий."""

    def __init__(
        self,
        repo_path: str = ".",
        anomaly_detector: AnomalyCorrelator = None,
        system_telemetry: SystemTelemetry = None
    ):
        self.repo_path = repo_path
        if anomaly_detector is None:
            self.anomaly_detector = AnomalyCorrelator(
                repo_path=self.repo_path,
                log_path="/tmp/anomalies.log",
                threshold=0.5,
                detector=None,
                logger=None
            )
        else:
            self.anomaly_detector = anomaly_detector

        if system_telemetry is None:
            self.system_telemetry = SystemTelemetry(
                repo_path=self.repo_path,
                anomaly_detector=self.anomaly_detector,
                autonomous_engine=None
            )
        else:
            self.system_telemetry = system_telemetry

    def generate_digest(self, execution_id=None) -> dict:
        """Генерирует дайджест стабильности, объединяя сводку телеметрии и результаты детектирования аномалий."""
        try:
            summary = self.system_telemetry.get_telemetry_summary()
            
            # Поддержка как реального интерфейса AnomalyCorrelator, так и моков из юнита
            if hasattr(self.anomaly_detector, "detect_anomalies"):
                anomalies = self.anomaly_detector.detect_anomalies()
            elif hasattr(self.anomaly_detector, "analyze_anomalies"):
                anomalies = self.anomaly_detector.analyze_anomalies()
            else:
                anomalies = []

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