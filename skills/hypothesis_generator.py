from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser


class HypothesisGeneratorError(Exception):
    """Кастомное исключение для модуля генерации гипотез."""
    pass


class HypothesisGenerator:
    def __init__(self, repo_path=None, git_inspector=None, lesson_parser=None):
        self.repo_path = repo_path

        if git_inspector is not None:
            self.git_inspector = git_inspector
        else:
            self.git_inspector = GitInspector(repo_path=self.repo_path)

        if lesson_parser is not None:
            self.lesson_parser = lesson_parser
        else:
            self.lesson_parser = LessonParser(git_inspector=self.git_inspector)

    def generate_hypotheses(self, max_commits=10):
        try:
            try:
                lessons = self.lesson_parser.extract_lessons(max_commits=max_commits)
            except TypeError:
                lessons = self.lesson_parser.extract_lessons()

            try:
                commits = self.git_inspector.get_commit_history(max_count=max_commits)
            except (TypeError, AttributeError):
                try:
                    commits = self.git_inspector.get_commit_history(limit=max_commits)
                except (TypeError, AttributeError):
                    try:
                        commits = self.git_inspector.get_commit_history()
                    except (TypeError, AttributeError):
                        try:
                            commits = self.git_inspector.get_history(limit=max_commits)
                        except (TypeError, AttributeError):
                            commits = self.git_inspector.get_history()

            if not lessons and not commits:
                return []

            hypotheses = []
            for lesson in lessons:
                hypotheses.append({
                    "id": lesson.get("id"),
                    "title": lesson.get("title"),
                    "commit": lesson.get("commit"),
                    "content": lesson.get("content"),
                    "priority_score": 10
                })

            for commit in commits:
                hypotheses.append({
                    "id": commit.get("hash"),
                    "title": commit.get("message"),
                    "priority_score": 5
                })

            return hypotheses
        except Exception as e:
            if isinstance(e, HypothesisGeneratorError):
                raise e
            raise HypothesisGeneratorError(str(e))

    def analyze_trends(self, file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
        return data

    def prioritize_hypotheses(self, hypotheses):
        return sorted(hypotheses, key=lambda x: x.get("priority_score", 0), reverse=True)