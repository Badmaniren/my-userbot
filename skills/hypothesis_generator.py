import uuid
import os


class HypothesisGeneratorError(Exception):
    """Custom exception for HypothesisGenerator errors."""
    pass


class HypothesisGenerator:
    def __init__(self, git_inspector, lesson_parser):
        self.git_inspector = git_inspector
        self.lesson_parser = lesson_parser

    def generate_hypotheses(self, max_commits=None):
        try:
            commits = self.git_inspector.get_commit_history(max_count=max_commits)
            lessons = self.lesson_parser.parse_lessons()
        except Exception as e:
            raise HypothesisGeneratorError(str(e))

        # Determine the repository path if available from git_inspector
        repo_path = getattr(self.git_inspector, "repo_path", ".")
        lesson_file_path = os.path.join(repo_path, "LESSONS.md")
        if os.path.exists(lesson_file_path):
            with open(lesson_file_path, "rb") as f:
                f.read()

        hypotheses = []

        for commit in commits:
            msg = commit.get("message", "")
            hypotheses.append({
                "id": uuid.uuid4().hex,
                "description": f"Improve stability based on commit: {msg}",
                "source": "git",
                "score": 50
            })

        for lesson in lessons:
            topic = lesson.get("topic", "")
            insights = lesson.get("insights", [])
            insight_str = ", ".join(str(i) for i in insights) if insights else ""
            hypotheses.append({
                "id": uuid.uuid4().hex,
                "description": f"Address lesson topic {topic} with insights {insight_str}",
                "source": "lesson",
                "score": 75
            })

        # Fallback if no specific data generated elements
        if not hypotheses:
            hypotheses.append({
                "id": uuid.uuid4().hex,
                "description": "General optimization hypothesis",
                "source": "fallback",
                "score": 10
            })

        return hypotheses

    def prioritize_hypotheses(self, hypotheses):
        return sorted(hypotheses, key=lambda x: x.get("score", 0), reverse=True)