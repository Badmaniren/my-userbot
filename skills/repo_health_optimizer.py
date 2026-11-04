from skills.repo_health_restorer import RepoHealthRestorer
from skills.vulnerability_analyzer import VulnerabilityAnalyzer


class RepoHealthOptimizer:
    """Модуль оптимизации репозитория на основе комбинирования аудита структуры,

    восстановления здоровья и анализа уязвимостей для непрерывного улучшения кодовой базы.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.restorer = RepoHealthRestorer(self.repo_path)
        self.vulnerability_analyzer = VulnerabilityAnalyzer(self.repo_path)

    def optimize_repository(self) -> dict:
        restoration_result = self.restorer.restore_and_protect()
        vulnerability_result = self.vulnerability_analyzer.run()
        return {
            "restoration": restoration_result,
            "vulnerabilities": vulnerability_result,
        }

    def process_optimization_stream(self, stream) -> dict:
        stream_restoration = self.restorer.comprehensive_health_restoration(stream)
        stream_vulnerabilities = self.vulnerability_analyzer.parse_stream_data(stream)
        return {
            "stream_restoration": stream_restoration,
            "stream_vulnerabilities": stream_vulnerabilities,
        }

    def run_optimization_routine(self) -> bool:
        routine_flag = self.restorer.execute_restoration_routine()
        self.vulnerability_analyzer.scan_vulnerabilities()
        return routine_flag

    def optimize(self) -> dict:
        return self.optimize_repository()

    def run(self) -> dict:
        return self.optimize_repository()