import os
import io

class PatchAnalyzerError(Exception):
    """Custom exception for patch analysis errors."""
    pass


class GitInspector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path


class PatchAnalyzer:
    def analyze(self, raw_patch: str) -> dict:
        if isinstance(raw_patch, bytes):
            try:
                raw_patch = raw_patch.decode("utf-8")
            except Exception:
                raw_patch = ""

        if not isinstance(raw_patch, str):
            raw_patch = str(raw_patch)

        affected_files = []
        new_files = []
        deleted_files = []
        total_added = 0
        total_removed = 0
        added_lines_list = []
        details_list = []

        lines = raw_patch.splitlines()
        current_file = None

        for line in lines:
            if line.startswith("diff --git"):
                parts = line.split(" b/")
                if len(parts) > 1:
                    current_file = parts[1]
                    if current_file not in affected_files:
                        affected_files.append(current_file)
            elif line.startswith("+++ b/"):
                fname = line[6:].strip()
                if fname and fname != "dev/null":
                    current_file = fname
                    if current_file not in affected_files:
                        affected_files.append(current_file)
            elif line.startswith("--- a/"):
                fname = line[6:].strip()
                if fname == "dev/null" and current_file:
                    if current_file not in new_files:
                        new_files.append(current_file)
            elif line.startswith("+++ /dev/null") and current_file:
                if current_file not in deleted_files:
                    deleted_files.append(current_file)
            elif line.startswith("+") and not line.startswith("+++"):
                total_added += 1
                added_lines_list.append(line[1:])
                details_list.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                total_removed += 1
                details_list.append(line[1:])

        complexity = float(total_added + total_removed)

        return {
            "affected_files": affected_files,
            "new_files": new_files,
            "deleted_files": deleted_files,
            "total_added": total_added,
            "total_removed": total_removed,
            "added_lines": "\n".join(added_lines_list),
            "details": "\n".join(details_list),
            "complexity": complexity,
            "files": affected_files,
            "additions": total_added,
            "deletions": total_removed,
            "diff_complexity": complexity
        }

    def analyze_stream(self, stream: io.IOBase) -> dict:
        content = stream.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")
        return self.analyze(content)

    def analyze_file(self, filepath: str) -> dict:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return self.analyze(content)

    def analyze_patch(self, raw_patch: str) -> dict:
        return self.analyze(raw_patch)

    def analyze_diff(self, raw_patch: str) -> dict:
        return self.analyze(raw_patch)

    def __call__(self, raw_patch: str) -> dict:
        return self.analyze(raw_patch)