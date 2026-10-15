import os
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

class SystemTelemetryError(Exception):
    """Исключение для ошибок модуля SystemTelemetry."""
    pass

class SystemTelemetry:
    """Модуль для сбора системных метрик и телеметрии выполнения автономных циклов."""
    
    def __init__(
        self, 
        repo_path: str, 
        anomaly_detector: Optional[Any] = None, 
        autonomous_engine: Optional[Any] = None
    ):
        self.repo_path = repo_path
        self.anomaly_detector = anomaly_detector
        self.autonomous_engine = autonomous_engine
        self.metrics: Dict[str, List[Any]] = {}
        self.snapshots: Dict[str, Dict[str, Any]] = {}

    def _validate_metric(self, name: str, value: Any) -> None:
        """Внутренний метод для валидации имени метрики и значения."""
        if not isinstance(name, str) or not name:
            raise SystemTelemetryError("Invalid metric name")
        if value is None:
            raise SystemTelemetryError("Metric value cannot be None")

    def record_metric(self, name: str, value: Any) -> None:
        """Запись метрики с защитой от молчаливого подавления исключений."""
        self._validate_metric(name, value)
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def get_metric_history(self, name: str) -> List[Any]:
        """Получение истории значений метрики."""
        if name not in self.metrics:
            raise SystemTelemetryError(f"Metric '{name}' not found")
        history = self.metrics[name]
        if history is None:
            raise TypeError(f"Metric history for '{name}' is None")
        return history

    def collect_snapshot(self, execution_id: str) -> Dict[str, Any]:
        """Сбор снимка текущей телеметрии."""
        if not execution_id:
            raise SystemTelemetryError("Execution ID cannot be empty")
        
        snapshot = {
            "execution_id": execution_id,
            "timestamp": time.time(),
            "repo_path": self.repo_path,
            "metrics": dict(self.metrics)
        }
        self.snapshots[execution_id] = snapshot
        return snapshot

    def export_stream(self, stream_id: str) -> Any:
        """Экспорт потока телеметрии."""
        file_path = Path(self.repo_path) / f"stream_{stream_id}.log"
        # Открытие файла через встроенную функцию, которая может быть замокана в тестах
        with open(file_path, "wb") as f:
            f.write(stream_id.encode('utf-8'))
        return open(file_path, "rb")

    def analyze_execution_telemetry(self, execution_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ телеметрии выполнения."""
        if not execution_id:
            raise SystemTelemetryError("Execution ID required for analysis")
        analysis = {
            "execution_id": execution_id,
            "status": "analyzed",
            "analyzed_data": data,
            "timestamp": time.time()
        }
        return analysis

    def detect_anomaly(self, metric_name: str, value: float) -> bool:
        """Определение аномалий по метрике с использованием anomaly_detector если доступен."""
        if self.anomaly_detector and hasattr(self.anomaly_detector, "detect"):
            try:
                return bool(self.anomaly_detector.detect(metric_name, value))
            except Exception as e:
                raise SystemTelemetryError(f"Anomaly detection failed: {e}") from e
        
        # Запасная логика на основе порогов, если детектор не задан
        history = self.metrics.get(metric_name, [])
        if not history:
            return False
        avg = sum(history) / len(history)
        return abs(value - avg) > (avg * 0.5) if avg != 0 else bool(value != 0)

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Получение общей сводки по всей телеметрии."""
        return {
            "repo_path": self.repo_path,
            "total_metrics": len(self.metrics),
            "total_snapshots": len(self.snapshots),
            "metrics_keys": list(self.metrics.keys())
        }