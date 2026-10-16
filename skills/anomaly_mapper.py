import re
from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.git_inspector import GitInspector


class AnomalyMapper:
    """Маппер аномалий на коммиты репозитория и изменения в файлах."""

    def __init__(self, anomaly_detector, git_inspector):
        self.anomaly_detector = anomaly_detector
        self.git_inspector = git_inspector

    def _correlate(self, anomaly, history):
        """Внутренний метод корреляции аномалии с историей коммитов."""
        if not history:
            return None
        return history[0]

    def _extract_files_from_diff(self, diff):
        """Извлекает список измененных файлов из диффа (dict или str)."""
        if not diff:
            return []
        if isinstance(diff, dict):
            return diff.get("files", [])
        if isinstance(diff, str):
            files = re.findall(r'^diff --git a/(.*?) b/', diff, re.MULTILINE)
            if not files:
                files = []
                for line in diff.splitlines():
                    if line.startswith('+++ b/'):
                        fname = line[6:].strip()
                        if fname and fname != '/dev/null':
                            files.append(fname)
            return files
        return []

    def _get_changed_files(self, commit_hash):
        """Возвращает список измененных файлов для коммита."""
        if not commit_hash:
            return []
        file_changes = []
        if hasattr(self.git_inspector, "get_changed_files_at_commit"):
            try:
                file_changes = self.git_inspector.get_changed_files_at_commit(commit_hash)
            except Exception:
                file_changes = []
        if not file_changes and hasattr(self.git_inspector, "get_changed_files"):
            try:
                file_changes = self.git_inspector.get_changed_files(commit_hash)
            except Exception:
                file_changes = []
        if not file_changes:
            try:
                diff = self.git_inspector.get_file_diff(commit_hash)
                file_changes = self._extract_files_from_diff(diff)
            except Exception:
                file_changes = []
        return file_changes or []

    def map_anomalies_to_commits(self):
        """Сопоставляет обнаруженные аномалии с коммитами и изменениями файлов."""
        anomalies_data = self.anomaly_detector.detect_anomalies()
        findings = anomalies_data.get("findings", [])
        status = anomalies_data.get("status")

        if not findings or status == "clean":
            return {"status": "clean", "mappings": []}

        history = self.git_inspector.get_commit_history()
        mappings = []

        for finding in findings:
            anomaly_id = finding.get("id")
            commit_hash = None
            affected_files = []

            if history:
                matched_commit = self._correlate(finding, history)
                if matched_commit:
                    if isinstance(matched_commit, dict):
                        commit_hash = matched_commit.get("hash")
                    else:
                        commit_hash = getattr(matched_commit, "hash", str(matched_commit))
                    affected_files = self._get_changed_files(commit_hash)

            mapping_entry = {
                "id": anomaly_id,
                "commit_hash": commit_hash,
            }
            if affected_files:
                mapping_entry["file"] = affected_files[0]
                mapping_entry["files"] = affected_files

            mappings.append(mapping_entry)

        return {"status": "mapped", "mappings": mappings}

    def map_anomaly_to_commit(self, metric_name, target_value):
        """Интеграционный метод для маппинга отдельной аномалии метрики на коммит."""
        history = self.git_inspector.get_commit_history()
        commit_hash = history[0]["hash"] if history else None

        file_changes = []
        if commit_hash:
            file_changes = self._get_changed_files(commit_hash)

        return {
            "commit_hash": commit_hash,
            "file_changes": file_changes,
            "metric": metric_name,
            "target_value": target_value
        }

    def analyze_content(self, commit_hash, file_path):
        """Анализирует содержимое файла в определенном коммите через потоки."""
        if hasattr(self.git_inspector, "read_file_at_commit"):
            content = self.git_inspector.read_file_at_commit(commit_hash, file_path)
            if isinstance(content, bytes):
                return content.decode("utf-8")
            return str(content)
        return ""
