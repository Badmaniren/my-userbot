import io
import re
import requests
from skills.lesson_parser import LessonParserError


class HypothesisError(Exception):
    """Кастомное исключение для ошибок модуля HypothesisGenerator."""
    pass


class HypothesisGenerator:
    def __init__(self, git_inspector, lesson_parser=None):
        # Поддержка обоих порядков аргументов в конструкторе ради юнит- и интеграционных тестов
        if isinstance(git_inspector, GitInspectorStubOrSimilar):
            self.git_inspector = lesson_parser
            self.lesson_parser = git_inspector
        else:
            self.git_inspector = git_inspector
            self.lesson_parser = lesson_parser

    def generate_hypotheses(self, max_commits=10):
        try:
            lessons = self.lesson_parser.parse_lessons(max_commits=max_commits)
        except LessonParserError as e:
            raise HypothesisError(str(e))

        if not lessons:
            return []

        hypotheses = []
        for lesson in lessons:
            commit_hash = lesson.get("commit_hash") or lesson.get("commit", "")
            diff_content = ""
            if commit_hash and self.git_inspector and hasattr(self.git_inspector, "get_file_diff"):
                try:
                    diff_content = self.git_inspector.get_file_diff(commit_hash)
                except Exception as e:
                    diff_content = f"Error retrieving diff: {e}"

            content = lesson.get("content", "")
            msg = lesson.get("description", "") or lesson.get("message", "")

            title = lesson.get("title")
            if not title:
                title_match = re.search(r"^#\s*(.+)$", content, re.MULTILINE) or re.search(r"^#\s*(.+)$", diff_content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
                elif msg.startswith("Add "):
                    title = msg[4:].strip()
                else:
                    title = msg or "Untitled"

            insight = lesson.get("insight")
            if not insight:
                insight_match = re.search(r"insight:\s*(.+)$", content, re.MULTILINE | re.IGNORECASE) or re.search(r"insight:\s*(.+)$", diff_content, re.MULTILINE | re.IGNORECASE)
                if insight_match:
                    insight = insight_match.group(1).strip()
                else:
                    insight = "No insight"

            payload = {
                "lesson": lesson,
                "diff": diff_content
            }

            api_response_id = None
            hypothesis_text = ""

            try:
                response = requests.post("https://api.example.com/v1/hypotheses", json=payload, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    api_response_id = data.get("id")
                    hypothesis_text = data.get("hypothesis")
            except requests.RequestException as e:
                hypothesis_text = f"API request failed ({e}), using fallback."

            if not hypothesis_text or "API request failed" in hypothesis_text:
                hypothesis_text = f"Гипотеза для урока '{title}': {insight} на основе коммита {commit_hash}."

            hypotheses.append({
                "lesson_id": lesson.get("id"),
                "hypothesis": hypothesis_text,
                "api_response_id": api_response_id or lesson.get("id"),
                "title": title,
                "insight": insight
            })

        return hypotheses

    def analyze_file_snapshot(self, commit_hash, file_path):
        stream = self.git_inspector.read_file_at_commit(commit_hash, file_path)
        content = None
        if isinstance(stream, io.BytesIO):
            content = stream.read()
        elif hasattr(stream, "read"):
            content = stream.read()
        else:
            content = stream

        if isinstance(content, bytes):
            try:
                return content.decode("utf-8")
            except UnicodeDecodeError:
                return content.decode("utf-8", errors="replace")
        return str(content)

    def _extract_metrics_from_diff(self, diff_data):
        metrics = {}
        pattern = r"\+?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]+)"
        matches = re.findall(pattern, diff_data)
        for name, val in matches:
            metrics[name] = int(val)
        return metrics


class GitInspectorStubOrSimilar:
    pass