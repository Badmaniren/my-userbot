import io
import json
from skills.hypothesis_generator import HypothesisGeneratorError

class EvolutionDashboardError(Exception):
    """Кастомное исключение для ошибок дашборда эволюции."""
    pass

class EvolutionDashboard:
    def __init__(self, git_inspector, hypothesis_generator, patch_executor, lesson_parser):
        self.git_inspector = git_inspector
        self.hypothesis_generator = hypothesis_generator
        self.patch_executor = patch_executor
        self.lesson_parser = lesson_parser

    def collect_metrics(self):
        try:
            commit_history = self.git_inspector.get_commit_history()
            lessons = self.lesson_parser.parse_lessons()
            hypotheses = self.hypothesis_generator.generate_hypotheses()
            patch_results = self.patch_executor.execute_from_lessons()

            return {
                "commit_history": commit_history,
                "lessons": lessons,
                "hypotheses": hypotheses,
                "patch_results": patch_results
            }
        except Exception as e:
            if isinstance(e, EvolutionDashboardError):
                raise e
            raise EvolutionDashboardError(str(e))

    def render_dashboard(self):
        metrics = self.collect_metrics()
        return json.dumps(metrics, ensure_ascii=False, indent=2, default=str)

    def export_report(self, filename):
        dashboard_data = self.render_dashboard()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(dashboard_data)
        return filename

    def stream_metrics(self):
        metrics = self.collect_metrics()
        content = json.dumps(metrics, ensure_ascii=False, default=str).encode('utf-8')
        return io.BytesIO(content)

    def get_evolution_metrics(self):
        return self.collect_metrics()

    def get_summary(self):
        return self.collect_metrics()