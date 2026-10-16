import io
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class AnomalyDetectorError(Exception):
    """Кастомное исключение для детектора аномалий."""
    pass

class AnomalyDetector:
    """
    Модуль для обнаружения аномалий в поведении системы и метриках 
    выполнения патчей на основе статистического анализа.
    """
    def __init__(
        self, 
        repo_path: str, 
        threshold: float = 5.0, 
        git_inspector: Optional[Any] = None, 
        patch_verifier: Optional[Any] = None
    ) -> None:
        self.repo_path = repo_path
        self.threshold = threshold
        self.git_inspector = git_inspector
        self.patch_verifier = patch_verifier
        self.history: List[Any] = []
        self._metric_history_dict: Dict[str, List[float]] = {}
        self._metric_entries_dict: Dict[str, List[Dict[str, Any]]] = {}

    def record_metric(self, metric_name: str, value: float) -> None:
        """Записывает метрику в историю для последующего анализа."""
        ts = time.time()
        if metric_name not in self._metric_history_dict:
            self._metric_history_dict[metric_name] = []
            self._metric_entries_dict[metric_name] = []
        self._metric_history_dict[metric_name].append(value)
        self._metric_entries_dict[metric_name].append({"timestamp": ts, "value": value})
        self.history.append(value)

    def get_metric_history(self, metric_name: str) -> List[float]:
        """Возвращает историю значений для указанной метрики."""
        return self._metric_history_dict.get(metric_name, [])

    def detect_anomaly(self, metric_name: str, target_value: float) -> bool:
        """Определяет, является ли целевое значение метрики аномалией относительно истории."""
        history = self.get_metric_history(metric_name)
        if not history:
            raise AnomalyDetectorError(f"No history found for metric: {metric_name}")
        
        mean_val = sum(history) / len(history)
        
        if abs(target_value - mean_val) > self.threshold or target_value > self.threshold * 2:
            return True
            
        return False

    def _fetch_execution_logs(self, execution_id: str) -> io.BytesIO:
        """Внутренний метод для получения логов выполнения (мокается в тестах)."""
        return io.BytesIO(f"execution_id: {execution_id}".encode('utf-8'))

    def analyze_execution_metrics(self, execution_id: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Анализирует метрики выполнения конкретного процесса/патча."""
        logs = self._fetch_execution_logs(execution_id)
        
        anomalies_detected = []
        for name, val in metrics.items():
            self.record_metric(name, val)
            if val > self.threshold * 5:
                anomalies_detected.append(name)

        return {
            "execution_id": execution_id,
            "anomalies_detected": anomalies_detected,
            "logs_size": len(logs.getvalue())
        }

    def batch_analyze_patches(self, batch_id: str, patch_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Выполняет пакетный анализ метрик патчей."""
        total_analyzed = len(patch_metrics)
        anomalies_count = 0
        
        for patch in patch_metrics:
            duration = patch.get("duration", 0.0)
            self.record_metric("batch_duration", duration)
            if duration > self.threshold:
                anomalies_count += 1

        return {
            "batch_id": batch_id,
            "total_analyzed": total_analyzed,
            "anomalies_count": anomalies_count
        }

    def detect_anomalies(self) -> Dict[str, Any]:
        """Интеграционный метод для обнаружения аномалий в репозитории."""
        commits_count = 0
        if self.git_inspector:
            try:
                history = self.git_inspector.get_commit_history(max_count=10)
                commits_count = len(history)
            except Exception:
                commits_count = 0

        res: Dict[str, Any] = {
            "status": "analyzed",
            "repo_path": self.repo_path,
            "commits_inspected": commits_count,
            "anomalies_found": []
        }

        for metric_name, entries in self._metric_entries_dict.items():
            if not entries:
                continue
            values = [e["value"] for e in entries]
            mean_val = sum(values) / len(values)
            metric_anomalies = []
            for entry in entries:
                val = entry["value"]
                # Detect spikes relative to the overall history or baseline mean
                if (val - mean_val) > self.threshold or val > (mean_val * 2 + self.threshold):
                    metric_anomalies.append({
                        "timestamp": entry["timestamp"],
                        "value": val,
                        "severity": (val - mean_val) / (self.threshold if self.threshold else 1.0)
                    })
            if metric_anomalies:
                res[metric_name] = metric_anomalies
                res["anomalies_found"].append(metric_name)

        return res