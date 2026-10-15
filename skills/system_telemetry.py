import json
import time

try:
    import psutil
except ImportError:
    psutil = None

from typing import List, Dict, Any, Optional

class SystemTelemetryError(Exception):
    """Кастомное исключение для ошибок модуля телеметрии."""
    pass

class SystemTelemetry:
    """Модуль для сбора системных метрик и телеметрии работы движка."""

    def __init__(self, repo_path: str, anomaly_detector: Optional[Any] = None):
        self.repo_path = repo_path
        self.anomaly_detector = anomaly_detector
        self.metrics_store: Dict[str, List[float]] = {}
        self.execution_logs: Dict[str, Dict[str, Any]] = {}
        self._timers: Dict[str, float] = {}

    def record_metric(self, metric_name: str, value: float) -> None:
        """Записывает значение метрики в хранилище."""
        if metric_name not in self.metrics_store:
            self.metrics_store[metric_name] = []
        self.metrics_store[metric_name].append(float(value))

    def get_metric_history(self, metric_name: str) -> List[float]:
        """Возвращает историю значений указанной метрики."""
        return self.metrics_store.get(metric_name, [])

    def collect_system_snapshot(self) -> Dict[str, Any]:
        """Собирает текущий снимок системных ресурсов."""
        if psutil is not None:
            cpu_p = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            snapshot = {
                "cpu_percent": float(cpu_p),
                "memory_percent": float(mem.percent),
                "memory_available": int(mem.available),
                "timestamp": time.time()
            }
        else:
            snapshot = {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "memory_available": 0,
                "timestamp": time.time()
            }
        return snapshot

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Собирает системные метрики и сохраняет их в хранилище."""
        snapshot = self.collect_system_snapshot()
        self.record_metric("cpu_percent", snapshot["cpu_percent"])
        self.record_metric("memory_percent", snapshot["memory_percent"])
        return snapshot

    def monitor_engine_health(self) -> Dict[str, Any]:
        """Мониторит здоровье движка на основе системного снимка."""
        snapshot = self.collect_system_snapshot()
        status = "healthy"
        if snapshot["cpu_percent"] > 90.0 or snapshot["memory_percent"] > 90.0:
            status = "degraded"
        return {
            "status": status,
            "metrics": snapshot,
            "timestamp": time.time()
        }

    def start_timer(self, timer_name: str) -> float:
        """Запускает таймер."""
        now = time.time()
        self._timers[timer_name] = now
        return now

    def stop_timer(self, timer_name: str) -> float:
        """Останавливает таймер и записывает результат в метрики."""
        if timer_name not in self._timers:
            return 0.0
        elapsed = time.time() - self._timers.pop(timer_name)
        self.record_metric(f"timer_{timer_name}", elapsed)
        return elapsed

    def track_execution(self, execution_id: str, metrics_payload: Dict[str, float]) -> Dict[str, Any]:
        """Отслеживает выполнение и анализирует метрики."""
        return self.analyze_execution_metrics(execution_id, metrics_payload)

    def log_evolution_cycle(self, cycle_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Логирует цикл эволюции."""
        log_entry = {
            "cycle_id": cycle_id,
            "payload": payload or {},
            "timestamp": time.time()
        }
        self.execution_logs[f"cycle_{cycle_id}"] = log_entry
        return log_entry

    def analyze_telemetry_trends(self, metric_name: str) -> Dict[str, Any]:
        """Анализирует тренды и базовую статистику по метрике."""
        history = self.get_metric_history(metric_name)
        if not history:
            return {
                "average": 0.0,
                "max": 0.0,
                "min": 0.0,
                "trend": "stable"
            }

        avg = sum(history) / len(history)
        mx = max(history)
        mn = min(history)

        trend = "stable"
        if len(history) >= 2:
            if history[-1] > history[0]:
                trend = "increasing"
            elif history[-1] < history[0]:
                trend = "decreasing"

        return {
            "average": float(avg),
            "max": float(mx),
            "min": float(mn),
            "trend": trend
        }

    def export_telemetry_report(self, file_path: str) -> bool:
        """Экспортирует отчет телеметрии в JSON файл."""
        try:
            report_data = {
                "repo_path": self.repo_path,
                "metrics_store": self.metrics_store,
                "timestamp": time.time()
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            return True
        except Exception as e:
            raise SystemTelemetryError(f"Failed to export telemetry report: {e}")

    def detect_anomaly(self, metric_name: str, value: float) -> bool:
        """Проверяет значение на аномальность через anomaly_detector, если он задан."""
        if self.anomaly_detector and hasattr(self.anomaly_detector, "detect"):
            return self.anomaly_detector.detect(metric_name, value)

        history = self.get_metric_history(metric_name)
        if not history:
            return False
        avg = sum(history) / len(history)
        if value > avg * 3 or value > 500.0:
            return True
        return False

    def analyze_execution_metrics(self, execution_id: str, metrics_payload: Dict[str, float]) -> Dict[str, Any]:
        """Анализирует пачку метрик конкретного выполнения и сохраняет результаты."""
        anomalies_found = {}
        for m_name, val in metrics_payload.items():
            self.record_metric(m_name, val)
            is_anom = self.detect_anomaly(m_name, val)
            anomalies_found[m_name] = is_anom

        analysis = {
            "execution_id": execution_id,
            "metrics_analyzed": len(metrics_payload),
            "anomalies": anomalies_found,
            "timestamp": time.time()
        }
        self.execution_logs[execution_id] = analysis
        return analysis

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Возвращает общую сводку по собранной телеметрии."""
        return {
            "repo_path": self.repo_path,
            "total_metrics_tracked": len(self.metrics_store),
            "total_executions_logged": len(self.execution_logs),
            "timestamp": time.time()
        }
