import os
import requests
from bs4 import BeautifulSoup
from skills.repo_auditor import RepoAuditor


class RepoHealthAnalyzer:
    def __init__(self):
        pass

    def fetch_and_analyze(self, url: str) -> dict:
        try:
            response = requests.get(url)
            data = response.json()
        except requests.exceptions.RequestException:
            raise

        repo_id = data.get("repo_id")
        metrics = data.get("metrics", {})

        return {
            "repo_id": repo_id,
            "metrics": metrics,
            "anomaly_detected": False
        }

    def evaluate_anomalies(self, codebase_metrics: dict, html_dump: str) -> dict:
        tag = codebase_metrics.get("tag")
        complexity_index = codebase_metrics.get("complexity_index", 0.0)
        threshold = codebase_metrics.get("threshold", 0.0)

        soup = BeautifulSoup(html_dump, 'html.parser')
        div = soup.find(id=tag)

        detected_value = float(div.text) if div and div.text else complexity_index
        critical_alert = detected_value > threshold

        return {
            "target_tag": tag,
            "critical_alert": critical_alert,
            "detected_value": detected_value
        }

    def process_health_stream(self, endpoint: str, stream) -> None:
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(str(e))

    def generate_optimization_patch(self, input_data: dict) -> dict:
        module = input_data.get("module")
        patch_uuid = input_data.get("patch_uuid")
        score = input_data.get("score", 0)

        action_code = "OPTIMAL" if score >= 50 else "REFACTOR_REQUIRED"

        return {
            "patch_uuid": patch_uuid,
            "target_module": module,
            "action_code": action_code
        }

    def analyze_health(self, repo_path: str, threshold: float, metrics: dict) -> dict:
        try:
            auditor = RepoAuditor(repo_path)
        except TypeError:
            auditor = RepoAuditor()

        try:
            audit_res = auditor.audit_repository(repo_path)
        except TypeError:
            audit_res = auditor.audit_repository()

        # Оценка здоровья на основе метрик
        score = 100.0
        anomalies_detected = []
        for k, v in metrics.items():
            if isinstance(v, (int, float)) and v > threshold:
                anomalies_detected.append(k)
                score -= 10.0

        if score < 0.0:
            score = 0.0

        return {
            "health_score": score,
            "anomalies_detected": anomalies_detected,
            "audit_details": audit_res
        }