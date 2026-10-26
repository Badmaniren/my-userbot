import io
import re
import os
import subprocess

from skills.patch_sanitizer import PatchSanitizer
from skills.code_sanitizer import CodeSanitizer


class PatchAnalyzerError(Exception):
    """Кастомное исключение для ошибок анализа патчей."""
    pass


class GitInspector:
    """Инспектор репозитория для получения diff через git."""
    def __init__(self, repo_dir: str):
        self.repo_dir = repo_dir

    def get_file_diff(self, commit_hash: str) -> str:
        try:
            result = subprocess.run(
                ["git", "show", "--unified=3", commit_hash],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise PatchAnalyzerError(f"Failed to get git diff: {e}")
        except OSError as e:
            raise PatchAnalyzerError(f"Failed to get git diff: {e}")
        except Exception as e:
            raise PatchAnalyzerError(f"Failed to get git diff: {e}")


class PatchAnalyzer:
    """Парсер и статический анализатор unified diff/патчей."""

    def __init__(self):
        self.patch_sanitizer = PatchSanitizer()
        self.code_sanitizer = CodeSanitizer()

    def _normalize_diff(self, diff_text) -> str:
        if hasattr(diff_text, "read"):
            content = diff_text.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
            diff_text = content

        if hasattr(self.patch_sanitizer, "sanitize"):
            try:
                if hasattr(diff_text, "read"):
                    return self.patch_sanitizer.sanitize(diff_text)
                elif isinstance(diff_text, (str, bytes)):
                    stream = io.StringIO(diff_text) if isinstance(diff_text, str) else io.BytesIO(diff_text)
                    return self.patch_sanitizer.sanitize(stream)
            except Exception:
                pass

        if isinstance(diff_text, bytes):
            return diff_text.decode("utf-8", errors="ignore")
        return str(diff_text)

    def parse(self, diff_text):
        if not isinstance(diff_text, str):
            raise PatchAnalyzerError("Invalid diff type, expected string")
        if not diff_text or not diff_text.strip():
            raise PatchAnalyzerError("Empty or whitespace-only diff")

        self.validate_structure(diff_text)

        files = []
        current_file = None
        current_chunk = None

        lines = diff_text.splitlines()
        for line in lines:
            if line.startswith("--- a/"):
                if current_file:
                    files.append(current_file)
                target_file = line[6:]
                current_file = {
                    "target_file": target_file,
                    "chunks": []
                }
            elif line.startswith("+++ b/"):
                if current_file and "target_file" not in current_file:
                    current_file["target_file"] = line[6:]
                elif not current_file:
                    current_file = {
                        "target_file": line[6:],
                        "chunks": []
                    }
            elif line.startswith("@@"):
                if current_file is None:
                    current_file = {"target_file": "unknown", "chunks": []}
                match = re.search(r"@@\s*-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s*@@", line)
                current_chunk = {
                    "header": line,
                    "old_count": 0,
                    "new_count": 0
                }
                current_file["chunks"].append(current_chunk)
            elif line.startswith("-") and not line.startswith("---"):
                if current_chunk is not None:
                    current_chunk["old_count"] += 1
            elif line.startswith("+") and not line.startswith("+++"):
                if current_chunk is not None:
                    current_chunk["new_count"] += 1

        if current_file and current_file not in files:
            files.append(current_file)

        return {"files": files}

    def validate_structure(self, diff_text):
        if not isinstance(diff_text, str):
            raise PatchAnalyzerError("Invalid diff type")
        if not diff_text.strip():
            raise PatchAnalyzerError("Empty diff")

        lines = diff_text.splitlines()
        has_file_header = any(l.startswith("--- ") or l.startswith("+++ ") for l in lines)
        has_hunk_header = any(l.startswith("@@") for l in lines)

        if not has_file_header and not has_hunk_header:
            raise PatchAnalyzerError("Invalid diff format: missing headers")

        hunk_header_pattern = re.compile(r"^@@\s*-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s*@@")

        in_hunk = False
        declared_old = 0
        declared_new = 0
        actual_old = 0
        actual_new = 0

        for line in lines:
            if line.startswith("@@"):
                if in_hunk:
                    if actual_old != declared_old or actual_new != declared_new:
                        raise PatchAnalyzerError("Hunk line count mismatch")
                match = hunk_header_pattern.match(line)
                if not match:
                    raise PatchAnalyzerError("Corrupted hunk header")
                
                try:
                    header_content = line.split("@@")[1].strip()
                    parts = header_content.split()
                    old_part = parts[0][1:]  # strip leading '-'
                    new_part = parts[1][1:]  # strip leading '+'

                    declared_old = int(old_part.split(",")[1]) if "," in old_part else 1
                    declared_new = int(new_part.split(",")[1]) if "," in new_part else 1
                except (ValueError, IndexError):
                    declared_old = 1
                    declared_new = 1
                
                in_hunk = True
                actual_old = 0
                actual_new = 0
            elif in_hunk:
                if line.startswith("-") and not line.startswith("---"):
                    actual_old += 1
                elif line.startswith("+") and not line.startswith("+++"):
                    actual_new += 1
                elif line.startswith(" ") or line == "":
                    actual_old += 1
                    actual_new += 1

        if in_hunk:
            if actual_old != declared_old or actual_new != declared_new:
                raise PatchAnalyzerError("Hunk line count mismatch")

    def get_statistics(self, diff_text):
        if not isinstance(diff_text, str):
            return {"files_changed": 0, "additions": 0, "deletions": 0, "total_changes": 0}
        
        files_changed = 0
        additions = 0
        deletions = 0

        lines = diff_text.splitlines()
        for line in lines:
            if line.startswith("--- a/"):
                files_changed += 1
            elif line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        if files_changed == 0 and (additions > 0 or deletions > 0):
            files_changed = 1

        return {
            "files_changed": files_changed,
            "additions": additions,
            "deletions": deletions,
            "total_changes": additions + deletions
        }

    def detect_syntax_risks(self, diff_text):
        if not isinstance(diff_text, str):
            return []

        risks = []
        lines = diff_text.splitlines()

        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                content = line[1:]
                
                if "<<<<<<<" in content or "=======" in content or ">>>>>>>" in content:
                    risks.append({
                        "type": "merge_conflict_marker",
                        "details": f"Merge conflict marker found: {content}"
                    })

                for dangerous in ["eval", "exec", "os.system"]:
                    if dangerous in content:
                        risks.append({
                            "type": "dangerous_call",
                            "details": f"Dangerous call '{dangerous}' found in line: {content}"
                        })

                open_brackets = content.count('(') + content.count('[') + content.count('{')
                close_brackets = content.count(')') + content.count(']') + content.count('}')
                if open_brackets != close_brackets:
                    if content.strip().endswith(',') or content.strip().endswith('(') or content.strip().endswith('['):
                        risks.append({
                            "type": "unbalanced_delimiter",
                            "details": f"Unbalanced or unclosed delimiter in line: {content}"
                        })

        return risks

    def analyze(self, diff_text):
        try:
            if diff_text is None:
                raise PatchAnalyzerError("Invalid diff input")
            
            sanitized_diff = self._normalize_diff(diff_text)

            if not isinstance(sanitized_diff, str) or not sanitized_diff.strip():
                raise PatchAnalyzerError("Invalid diff input")

            self.validate_structure(sanitized_diff)
            parsed = self.parse(sanitized_diff)
            stats = self.get_statistics(sanitized_diff)
            risks = self.detect_syntax_risks(sanitized_diff)

            file_names = [f.get("target_file", "") for f in parsed.get("files", [])]
            all_chunks = []
            for f in parsed.get("files", []):
                all_chunks.extend(f.get("chunks", []))

            return {
                "parsed": parsed,
                "statistics": stats,
                "risks": risks,
                "syntax_risks": risks,
                "is_valid": True,
                "files": file_names,
                "additions": stats["additions"],
                "deletions": stats["deletions"],
                "chunks": all_chunks,
                "errors": []
            }
        except (PatchAnalyzerError, TypeError, ValueError) as e:
            return {
                "is_valid": False,
                "errors": [str(e)],
                "syntax_risks": [],
                "statistics": {"files_changed": 0, "additions": 0, "deletions": 0, "total_changes": 0}
            }

    def analyze_stream(self, stream):
        content = stream.read()
        return self.analyze(content)

    def analyze_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.analyze(content)