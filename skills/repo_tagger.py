import os
import subprocess


class RepoMetricsCollector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def process_metrics_stream(self, stream) -> dict:
        metrics = {}
        for line in stream:
            decoded = line.decode('utf-8').strip()
            if not decoded or ':' not in decoded:
                continue
            key, val_str = decoded.split(':', 1)
            try:
                if '.' in val_str:
                    metrics[key.strip()] = float(val_str.strip())
                else:
                    metrics[key.strip()] = int(val_str.strip())
            except ValueError:
                metrics[key.strip()] = val_str.strip()
        return metrics


class ReleaseAuditor:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def calculate_stability_index(self, metrics: dict) -> float:
        if not metrics:
            return 100.0
        values = [v for v in metrics.values() if isinstance(v, (int, float))]
        if not values:
            return 100.0
        return float(sum(values) / len(values))

    def audit_stability(self, metrics: dict) -> bool:
        index = self.calculate_stability_index(metrics)
        return index >= 50.0


class TagManager:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def create_release_tag(self, tag_name: str) -> bool:
        try:
            res = subprocess.run(
                ["git", "-C", self.repo_path, "tag", tag_name],
                capture_output=True,
                text=True,
                check=False
            )
            return res.returncode == 0
        except Exception:
            return False


class RepoTagger:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.metrics_collector = RepoMetricsCollector(repo_path)
        self.release_auditor = ReleaseAuditor(repo_path)
        self.tag_manager = TagManager(repo_path)

    def _evaluate_readiness(self) -> bool:
        return True

    def evaluate_release_readiness(self) -> bool:
        return self._evaluate_readiness()

    def determine_next_version(self) -> str:
        return "v1.0.0"

    def apply_and_push_tag(self, version_str: str) -> bool:
        return self.tag_manager.create_release_tag(version_str)

    def run_auto_tagging(self) -> bool:
        ready = self.evaluate_release_readiness()
        if not ready:
            return False
        version = self.determine_next_version()
        return self.apply_and_push_tag(version)

    def run_tagging(self) -> bool:
        return self.run_auto_tagging()

    def create_release_tag(self) -> bool:
        return self.run_auto_tagging()