import io
import os
from skills.git_inspector import GitInspector


class GitMetricExtractorError(Exception):
    """Кастомное исключение для ошибок GitMetricExtractor."""
    pass


class GitMetricExtractor:
    def __init__(self, repo_path=None, inspector=None, git_inspector=None):
        if repo_path is not None and not isinstance(repo_path, str):
            raise GitMetricExtractorError("Invalid repo_path type")
        if repo_path == "":
            raise GitMetricExtractorError("Empty repo_path")

        self.repo_path = repo_path
        
        if git_inspector is not None:
            self.inspector = git_inspector
        elif inspector is not None:
            self.inspector = inspector
        elif repo_path is not None:
            try:
                self.inspector = GitInspector(repo_path)
            except Exception as e:
                raise GitMetricExtractorError(str(e))
        else:
            raise GitMetricExtractorError("Neither repo_path nor inspector provided")

    def parse_diff_stat(self, raw_numstat: str) -> dict:
        if not isinstance(raw_numstat, str):
            raw_numstat = str(raw_numstat)

        additions = 0
        deletions = 0
        files_changed = []

        for line in raw_numstat.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                adds_str, dels_str, file_path = parts[0], parts[1], parts[2]
                if adds_str == "-" or dels_str == "-":
                    # Бинарный файл
                    adds = 0
                    dels = 0
                else:
                    try:
                        adds = int(adds_str)
                        dels = int(dels_str)
                    except ValueError:
                        adds = 0
                        dels = 0

                additions += adds
                deletions += dels
                if file_path not in files_changed:
                    files_changed.append(file_path)

        return {
            "additions": additions,
            "deletions": deletions,
            "total_churn": additions + deletions,
            "files_changed": files_changed
        }

    def parse_diff_stream(self, stream) -> dict:
        if hasattr(stream, "read"):
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
            return self.parse_diff_stat(content)
        return self.parse_diff_stat("")

    def extract_commit_metrics(self, commit_hash: str) -> dict:
        if not commit_hash:
            raise GitMetricExtractorError("Invalid commit hash")
        
        try:
            raw_diff = self.inspector.get_file_diff(commit_hash)
        except Exception as e:
            raise GitMetricExtractorError(str(e))

        parsed = self.parse_diff_stat(raw_diff)
        return {
            "commit_hash": commit_hash,
            "additions": parsed["additions"],
            "deletions": parsed["deletions"],
            "total_churn": parsed["total_churn"],
            "files_changed": parsed["files_changed"],
            "insertions": parsed["additions"],
        }

    def calculate_churn_rate(self, total_churn: int, total_commits: int) -> float:
        if total_churn < 0 or total_commits < 0:
            raise GitMetricExtractorError("Negative values are not allowed")
        if total_commits == 0 or total_churn == 0:
            return 0.0
        return round(float(total_churn) / total_commits, 4)

    def extract_history_metrics(self, max_count: int = 100) -> dict:
        try:
            commits = self.inspector.get_commit_history(max_count)
        except Exception as e:
            raise GitMetricExtractorError(str(e))

        commits_analyzed = len(commits)
        total_additions = 0
        total_deletions = 0
        file_frequencies = {}
        modified_files_set = set()

        for commit_hash in commits:
            raw_diff = self.inspector.get_file_diff(commit_hash)
            parsed = self.parse_diff_stat(raw_diff)
            total_additions += parsed["additions"]
            total_deletions += parsed["deletions"]
            for f in parsed["files_changed"]:
                modified_files_set.add(f)
                file_frequencies[f] = file_frequencies.get(f, 0) + 1

        total_churn = total_additions + total_deletions
        churn_rate = self.calculate_churn_rate(total_churn, commits_analyzed)

        return {
            "commits_analyzed": commits_analyzed,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_churn": total_churn,
            "churn_rate": churn_rate,
            "modified_files": sorted(list(modified_files_set)),
            "file_frequencies": file_frequencies
        }

    def get_hotspot_files(self, file_frequencies: dict, top_n: int = 5) -> list:
        sorted_files = sorted(file_frequencies.items(), key=lambda x: x[1], reverse=True)
        return sorted_files[:top_n]

    def extract_metrics(self, max_count: int = 100) -> dict:
        try:
            commits = self.inspector.get_commit_history(max_count)
        except Exception as e:
            raise GitMetricExtractorError(str(e))

        total_commits = len(commits)
        lines_added = 0
        lines_deleted = 0
        modified_files_set = set()
        commit_metrics = []

        for commit_hash in commits:
            raw_diff = self.inspector.get_file_diff(commit_hash)
            parsed = self.parse_diff_stat(raw_diff)
            lines_added += parsed["additions"]
            lines_deleted += parsed["deletions"]
            for f in parsed["files_changed"]:
                modified_files_set.add(f)
            
            commit_metrics.append({
                "commit_hash": commit_hash,
                "files_changed": parsed["files_changed"],
                "insertions": parsed["additions"],
                "deletions": parsed["deletions"],
                "total_churn": parsed["total_churn"],
            })

        total_churn = lines_added + lines_deleted
        churn_rate = self.calculate_churn_rate(total_churn, total_commits)

        return {
            "total_commits": total_commits,
            "modified_files": sorted(list(modified_files_set)),
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "churn_rate": churn_rate,
            "commit_metrics": commit_metrics,
        }