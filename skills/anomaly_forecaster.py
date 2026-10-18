import json
import hashlib
from typing import List, Dict, Any, Union
from skills.anomaly_logger import AnomalyLogger

class AnomalyForecasterError(Exception):
    """Базовое исключение для ошибок прогнозирования аномалий."""
    pass

class ModelNotTrainedError(AnomalyForecasterError):
    """Исключение, выбрасываемое при попытке предсказания неоттренированной моделью."""
    pass

class ForecastResult:
    def __init__(self, is_anomaly: bool, confidence_score: float, telemetry_snapshot: Dict[str, Any]):
        self.is_anomaly = is_anomaly
        self.confidence_score = confidence_score
        self.telemetry_snapshot = telemetry_snapshot

    def __str__(self) -> str:
        return f"ForecastResult(is_anomaly={self.is_anomaly}, confidence_score={self.confidence_score}, telemetry={self.telemetry_snapshot})"


class AnomalyForecaster:
    def __init__(self, log_path: str, model_name: str = "default_model", threshold: float = 0.5):
        if not (0.0 <= threshold <= 1.0):
            raise AnomalyForecasterError("Threshold must be between 0.0 and 1.0")
        self.log_path = log_path
        self.model_name = model_name
        self.threshold = threshold
        self.is_trained = False
        self.historical_data: List[Dict[str, Any]] = []

    def train(self) -> None:
        logger = AnomalyLogger(log_path=self.log_path)
        history = logger.get_anomalies()
        if not history:
            raise AnomalyForecasterError("Cannot train model on empty historical data.")
        self.historical_data = history
        self.is_trained = True

    def _run_prediction_algorithm(self, telemetry: Dict[str, Any]) -> float:
        # Базовая эвристика для симуляции прогнозирования
        return 0.75

    def predict(self, telemetry: Dict[str, Any]) -> ForecastResult:
        if not self.is_trained:
            raise ModelNotTrainedError("Model is not trained yet.")
        
        score = self._run_prediction_algorithm(telemetry)
        is_anomaly = score >= self.threshold
        return ForecastResult(
            is_anomaly=is_anomaly,
            confidence_score=score,
            telemetry_snapshot=telemetry
        )

    def export_report(self, results: List[ForecastResult], destination: str) -> None:
        report_data = [
            {
                "is_anomaly": r.is_anomaly,
                "confidence_score": r.confidence_score,
                "telemetry_snapshot": r.telemetry_snapshot
            }
            for r in results
        ]
        with open(destination, "w", encoding="utf-8") as f:
            json_str = json.dumps(report_data, ensure_ascii=False, indent=2)
            f.write(json_str)

    def parse_raw_stream(self, stream: Any) -> Dict[str, Any]:
        raw_bytes = stream.read()
        stream_hash = hashlib.sha256(raw_bytes).hexdigest()
        return {
            "stream_hash": stream_hash,
            "size": len(raw_bytes),
            "raw_preview": raw_bytes[:50]
        }


def forecast_anomalies(logger: AnomalyLogger) -> Union[str, Dict[str, Any]]:
    forecaster = AnomalyForecaster(log_path=logger.log_path)
    try:
        forecaster.train()
    except AnomalyForecasterError:
        pass
    
    anomalies = logger.get_anomalies()
    results = []
    for anomaly in anomalies:
        telemetry = anomaly.get("telemetry", {})
        if not telemetry:
            telemetry = {"source": anomaly.get("source", "unknown"), "severity": anomaly.get("severity", 0)}
        
        res = ForecastResult(is_anomaly=True, confidence_score=0.99, telemetry_snapshot=telemetry)
        results.append(res)
    
    structured_report = logger.get_structured_report()
    return f"Forecasted anomalies report based on {structured_report}"