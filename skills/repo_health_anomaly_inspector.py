from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class RepoHealthAnomalyInspector:
    """
    Модуль глубокой судебной аналитики и поиска корневых причин сбоев репозитория.
    Выполняет анализ метрик здоровья, детекцию аномалий и логирование результатов.
    """

    def __init__(self, pulse_engine=None):
        self.pulse_engine = pulse_engine if pulse_engine is not None else RepoHealthPulseEngine()
        self.logger = RepoLogger(repo_path=".")

    def inspect(self, repo_id=None, pulse_payload=None, threshold=None):
        # Если payload не передан, пытаемся получить его из движка пульса
        if pulse_payload is None:
            if repo_id is None:
                repo_id = "default-repo"
            
            if hasattr(self.pulse_engine, "get_pulse") and callable(getattr(self.pulse_engine, "get_pulse")):
                pulse_payload = self.pulse_engine.get_pulse(repo_id)
            elif hasattr(self.pulse_engine, "pulse") and callable(getattr(self.pulse_engine, "pulse")):
                pulse_payload = self.pulse_engine.pulse(repo_id)
            else:
                pulse_payload = {}

        if pulse_payload is None:
            pulse_payload = {}

        if not isinstance(pulse_payload, dict):
            pulse_payload = {}

        # Определяем идентификатор репозитория
        if repo_id is None:
            repo_id = pulse_payload.get("repo_id", "default-repo")

        metrics = pulse_payload.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = {}

        anomalies = []
        deviation_score = 0.0

        # Оптимизированный обход метрик и анализ на аномалии
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                f_val = float(value)
                if f_val < 0:
                    anomalies.append({
                        "metric": metric_name,
                        "value": f_val,
                        "deviation": "negative"
                    })
                    deviation_score += abs(f_val)
                elif threshold is not None and f_val > float(threshold):
                    anomalies.append({
                        "metric": metric_name,
                        "value": f_val,
                        "deviation": "high"
                    })
                    deviation_score += f_val - float(threshold)

        is_anomaly = len(anomalies) > 0

        # Расширенное логирование результатов судебной инспекции
        if hasattr(self.logger, "info"):
            self.logger.info(
                f"Inspected repo_id: {repo_id}, status: inspected, "
                f"is_anomaly: {is_anomaly}, anomalies_count: {len(anomalies)}, "
                f"deviation_score: {deviation_score}"
            )

        return {
            "repo_id": repo_id,
            "status": "inspected",
            "is_anomaly": is_anomaly,
            "anomalies": anomalies,
            "deviation_score": deviation_score
        }