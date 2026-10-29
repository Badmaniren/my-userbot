import io
import os
import re


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
            except UnicodeDecodeError:
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
                    if current_file == "dev/null":
                        a_parts = line.split(" a/")
                        if len(a_parts) > 1:
                            sub = a_parts[1].split(" b/")[0]
                            current_file = sub
                            if current_file and current_file not in deleted_files:
                                deleted_files.append(current_file)
                    else:
                        parts_a = line.split(" a/")
                        if len(parts_a) > 1:
                            a_file = parts_a[1].split(" b/")[0]
                            if a_file == "dev/null":
                                if current_file and current_file not in new_files:
                                    new_files.append(current_file)

                    if current_file and current_file != "dev/null" and current_file not in affected_files:
                        affected_files.append(current_file)
            elif line.startswith("--- "):
                fname = line[4:].strip()
                if fname.startswith("a/"):
                    fname = fname[2:]
                if fname != "dev/null" and fname:
                    if current_file is None or current_file == "dev/null":
                        current_file = fname
                    if current_file and current_file not in affected_files:
                        affected_files.append(current_file)
            elif line.startswith("+++ "):
                fname = line[4:].strip()
                if fname.startswith("b/"):
                    fname = fname[2:]
                if fname == "dev/null":
                    if current_file and current_file not in deleted_files:
                        deleted_files.append(current_file)
                else:
                    current_file = fname
                    if current_file and current_file not in affected_files:
                        affected_files.append(current_file)
            elif line.startswith("+++ /dev/null"):
                if current_file and current_file not in deleted_files:
                    deleted_files.append(current_file)
            elif line.startswith("new file mode"):
                if current_file and current_file not in new_files:
                    new_files.append(current_file)
            elif line.startswith("deleted file mode"):
                if current_file and current_file not in deleted_files:
                    deleted_files.append(current_file)
            elif line.startswith("@@"):
                hunk_match = re.match(r"^@@\s*-[0-9,]+\s+\+[0-9,]+\s*(?:@@)?\s*", line)
                remainder = line[hunk_match.end():] if hunk_match else line
                if remainder.startswith("+") and not remainder.startswith("+++"):
                    total_added += 1
                    added_lines_list.append(remainder[1:])
                    details_list.append(remainder[1:])
                elif remainder.startswith("-") and not remainder.startswith("---"):
                    total_removed += 1
                    details_list.append(remainder[1:])
            elif line.startswith("+") and not line.startswith("+++"):
                total_added += 1
                added_lines_list.append(line[1:])
                details_list.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                total_removed += 1
                details_list.append(line[1:])

        for nf in new_files:
            if nf not in affected_files:
                affected_files.append(nf)
        for df in deleted_files:
            if df not in affected_files:
                affected_files.append(df)

        complexity = float(total_added + total_removed)

        return {
            "affected_files": affected_files,
            "new_files": new_files,
            "deleted_files": deleted_files,
            "total_added": total_added,
            "total_removed": total_removed,
            "added_lines": total_added,
            "deleted_lines": total_removed,
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


def analyze(raw_patch: str) -> dict:
    return PatchAnalyzer().analyze(raw_patch)