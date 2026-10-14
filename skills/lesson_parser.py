import os
import re

class LessonParser:
    def __init__(self, git_inspector=None):
        self.git_inspector = git_inspector

    def parse(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self._parse_content(content)

    def _parse_content(self, content):
        if not isinstance(content, str):
            raise ValueError("Content must be a string")

        match = re.search(r'(?:Lesson\s*)?ID:\s*([^\s|\n]+)', content, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid lesson format: missing ID")

        lesson_id = match.group(1).strip()
        return {
            'id': lesson_id,
            'raw_text': content,
            'content': content
        }

    def get_context_for_file(self, file_path):
        history = []
        diff_data = ""
        if self.git_inspector:
            changes = self.git_inspector.get_latest_changes()
            commit_hash = None
            if isinstance(changes, list):
                for item in changes:
                    if isinstance(item, dict) and (item.get('file') == file_path or 'hash' in item):
                        commit_hash = item.get('hash')
                        break
            elif isinstance(changes, dict):
                commit_hash = changes.get('hash')

            if not commit_hash and hasattr(self.git_inspector, 'get_commit_history'):
                hist = self.git_inspector.get_commit_history()
                if hist and isinstance(hist, list) and len(hist) > 0:
                    commit_hash = hist[0].get('hash') if isinstance(hist[0], dict) else getattr(hist[0], 'hexsha', str(hist[0]))

            if commit_hash:
                history.append(commit_hash)
                diff_data = self.git_inspector.get_file_diff(commit_hash)

        return {
            'history': history,
            'diff': diff_data,
            'file': file_path
        }

    def analyze_file_history(self, target_file):
        if self.git_inspector and hasattr(self.git_inspector, 'get_history'):
            return self.git_inspector.get_history(target_file)
        return []

    def parse_latest_change(self, commit_hash):
        if not self.git_inspector:
            raise ValueError("Git inspector not configured")

        diff = self.git_inspector.get_file_diff(commit_hash)

        file_paths = re.findall(r'diff --git a/(.*?) b/(.*)', diff)

        content = ""
        if file_paths and hasattr(self.git_inspector, 'read_file_at_commit'):
            target_path = file_paths[0][1]
            content = self.git_inspector.read_file_at_commit(commit_hash, target_path)

        if not content:
            content = diff

        return self._parse_content(content)

    def parse_lesson_history(self, *args, **kwargs):
        return []

    def extract_error_patterns(self, *args, **kwargs):
        return []

    def prepare_hypothesis_data(self, *args, **kwargs):
        return {}
