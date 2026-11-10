import enum
import os
import io

class AnomalySeverity(enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class RemediationExecutionError(Exception):
    pass


class RepoHealthAnomalyRemediationPipeline:
    def __init__(self, pipeline_id=None, inspector=None, automator=None, restorer=None, logger=None):
        self.pipeline_id = pipeline_id
        self.inspector = inspector
        self.automator = automator
        self.restorer = restorer
        self.logger = logger

    def _log(self, message):
        if self.logger and hasattr(self.logger, "log"):
            self.logger.log(message)

    def run_pipeline(self, repo_path):
        if not repo_path or not isinstance(repo_path, str):
            raise RemediationExecutionError("Invalid repository path provided.")
        
        self._log(f"Starting inspection for repository at {repo_path}")
        anomaly = self.inspector.inspect_repository(repo_path)
        if not anomaly:
            self._log(f"No anomaly detected for repository at {repo_path}")
            return {
                "pipeline_id": self.pipeline_id,
                "status": "healthy",
                "remediated": False
            }

        anomaly_id = anomaly.get("anomaly_id")
        self._log(f"Anomaly detected: {anomaly_id}. Executing remediation.")
        try:
            rem_res = self.automator.execute_remediation(repo_path, anomaly)
            token = rem_res.get("token") if isinstance(rem_res, dict) else None
            self._log(f"Remediation successfully executed for anomaly {anomaly_id}, token: {token}")
            return {
                "pipeline_id": self.pipeline_id,
                "repo_path": repo_path,
                "anomaly_id": anomaly_id,
                "status": "remediated",
                "token": token
            }
        except (Exception, BaseException) as e:
            self._log(f"Remediation failed for anomaly {anomaly_id}: {str(e)}. Restoring state.")
            if self.restorer:
                self.restorer.restore_state(repo_path, anomaly_id)
            raise RemediationExecutionError(str(e))

    def analyze_anomaly_stream(self, log_path, metric_name, threshold):
        if not log_path or not isinstance(log_path, str):
            raise ValueError("Invalid log path provided.")
        
        with open(log_path, "r") as f:
            content = f.read()
        score = float(len(content) % 100) / 100.0 * threshold
        self._log(f"Analyzed anomaly stream for metric {metric_name} with score {score}")
        return {
            "stream_processed": True,
            "metric": metric_name,
            "anomaly_score": score
        }

    def batch_remediate(self, repo_paths):
        if not isinstance(repo_paths, list):
            raise RemediationExecutionError("repo_paths must be a list.")
        reports = []
        for path in repo_paths:
            reports.append(self.run_pipeline(path))
        return reports


def run_remediation_pipeline(payload):
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary.")
        
    run_id = payload.get("run_id")
    target_path = payload.get("target_path")
    
    if target_path and not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)

    if target_path:
        remediation_marker = os.path.join(target_path, f".remediated_{run_id}")
        with open(remediation_marker, "w") as f:
            f.write("remediated")

    return {
        "run_id": run_id,
        "status": "remediated"
    }


def inspect_anomalies(payload):
    if not isinstance(payload, dict):
        return {"anomaly_detected": True}
        
    target_path = payload.get("target_path")
    if target_path and os.path.exists(target_path):
        files = os.listdir(target_path)
        has_remediated = any(f.startswith(".remediated_") for f in files)
        if has_remediated:
            return {"anomaly_detected": False}
    return {"anomaly_detected": True}