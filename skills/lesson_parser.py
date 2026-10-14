import subprocess
import os
import re
import io

class GitInspector:
    def __init__(self, repo_path="."):
        self.repo_path = repo_path

    def _run_git(self, args):
        cmd = ["git", "-C", self.repo_path] + args
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        return result.stdout

    def read_file_at_commit(self, commit_hash, file_path):
        cmd = ["show", f"{commit_hash}:{file_path}"]
        result = subprocess.run(["git", "-C", self.repo_path] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise Exception(result.stderr.strip() or "Error reading file at commit")
        return result.stdout

    def read_file_stream(self, commit_hash, file_path):
        content = self.read_file_at_commit(commit_hash, file_path)
        return io.BytesIO(content.encode('utf-8'))

    def get_commit_history(self, max_count=10):
        output = self._run_git(["log", f"-n", str(max_count), "--format=%H - %s"])
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        return lines

    def get_file_diff(self, commit_hash="HEAD"):
        output = self._run_git(["show", commit_hash])
        return output

    def get_latest_changes(self):
        output = self._run_git(["diff", "HEAD~1", "HEAD"])
        if not output.strip():
            output = self._run_git(["show", "HEAD"])
        return output


class LessonParser:
    def __init__(self, git_inspector=None, repo_path="."):
        self.git_inspector = git_inspector if git_inspector else GitInspector(repo_path=repo_path)

    def parse_lesson_file(self, commit_hash, file_path):
        content = self.git_inspector.read_file_at_commit(commit_hash, file_path)

        lesson_id_match = re.search(r"(?:Урок|Lesson ID[:]?)\s*([a-zA-Z0-9\-]+)", content, re.IGNORECASE)
        lesson_id = lesson_id_match.group(1) if lesson_id_match else "unknown"

        title_match = re.search(r"^(#\s+.*)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else f"Lesson {lesson_id}"

        return {
            "lesson_id": lesson_id,
            "title": title,
            "raw_content": content
        }

    def parse_stream(self, commit_hash, file_path):
        stream = self.git_inspector.read_file_stream(commit_hash, file_path)
        return stream.read().decode('utf-8')

    def extract_history_context(self, file_path):
        commits = self.git_inspector.get_commit_history(max_count=10)
        diffs = []
        for commit in commits:
            h = commit.split()[0]
            diffs.append(self.git_inspector.get_file_diff(h))
        return "\n".join(diffs)

    def parse_lesson_context(self, raw_data):
        return raw_data