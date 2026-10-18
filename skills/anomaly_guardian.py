from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.anomaly_reactor import AutonomousReactorEngine
from skills.git_inspector import GitInspector
from skills.patch_verifier import PatchVerifier


class AnomalyGuardianError(Exception):
    """Кастомное исключение для ошибок AnomalyGuardian."""
    pass


class AnomalyGuardian:
    def __init__(self, repo_path=None, threshold=0.5, detector=None, reactor=None, git_inspector=None, patch_verifier=None):
        self.repo_path = repo_path
        self.threshold = threshold
        self.git_inspector = git_inspector if git_inspector is not None else (GitInspector(repo_path) if repo_path else None)
        self.patch_verifier = patch_verifier if patch_verifier is not None else (PatchVerifier(repo_path, self.git_inspector, None) if repo_path and self.git_inspector else None)

        if detector is not None:
            self.detector = detector
        else:
            self.detector = AnomalyDetector(
                repo_path=self.repo_path,
                threshold=self.threshold,
                git_inspector=self.git_inspector,
                patch_verifier=self.patch_verifier
            )

        if reactor is not None:
            self.reactor = reactor
        else:
            self.reactor = AutonomousReactorEngine()

    def record_metric(self, metric_name: str, value: float):
        try:
            self.detector.record_metric(metric_name, value)
        except AnomalyDetectorError as e:
            raise AnomalyGuardianError(str(e)) from e

    def guard_execution(self, metric_name: str, target_value: float) -> bool:
        try:
            is_anomaly = self.detector.detect_anomaly(metric_name, target_value)
            if is_anomaly:
                self.reactor.handle_anomaly(metric_name, target_value)
            return is_anomaly
        except AnomalyDetectorError as e:
            raise AnomalyGuardianError(str(e)) from e

    def analyze_and_suppress(self, execution_id: str, metrics: dict) -> dict:
        try:
            analysis_result = self.detector.analyze_execution_metrics(execution_id, metrics)

            if isinstance(analysis_result, dict) and "anomalies_detected" in analysis_result:
                anomalies = analysis_result["anomalies_detected"]
                for anomaly_metric in anomalies:
                    target_val = metrics.get(anomaly_metric, 0.0)
                    self.reactor.handle_anomaly(anomaly_metric, target_val)
                return analysis_result

            for metric, is_anomaly in analysis_result.items():
                if is_anomaly:
                    target_val = metrics.get(metric, 0.0)
                    self.reactor.handle_anomaly(target_val if isinstance(metric, float) else metric, target_val)
            return analysis_result
        except AnomalyDetectorError as e:
            raise AnomalyGuardianError(str(e)) from e

    def process_and_mitigate(self, metric_name: str, target_value: float, execution_id: str, metrics: dict) -> dict:
        try:
            analysis_result = self.analyze_and_suppress(execution_id, metrics)

            if isinstance(analysis_result, dict) and "anomalies_detected" in analysis_result:
                is_anomaly = metric_name in analysis_result["anomalies_detected"]
            else:
                is_anomaly = analysis_result.get(metric_name, False)

            if not is_anomaly:
                is_anomaly = self.guard_execution(metric_name, target_value)

            return {
                "mitigated": True,
                "anomaly_detected": is_anomaly,
                "analysis": analysis_result
            }
        except AnomalyDetectorError as e:
            raise AnomalyGuardianError(str(e)) from e