from skills import repo_security_gateway
from skills import vulnerability_analyzer


class RepoSecurityPipeline:
    """
    Модуль интеграции шлюза безопасности и анализатора уязвимостей.
    Обеспечивает автоматическое прерывание CI/CD при обнаружении критических угроз.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self._gateway = None
        self._analyzer = None

    @property
    def gateway(self):
        if self._gateway is not None:
            return self._gateway
        return repo_security_gateway.RepoSecurityGateway(self.repo_path)

    @gateway.setter
    def gateway(self, value):
        self._gateway = value

    @property
    def analyzer(self):
        if self._analyzer is not None:
            return self._analyzer
        return vulnerability_analyzer.VulnerabilityAnalyzer(self.repo_path)

    @analyzer.setter
    def analyzer(self, value):
        self._analyzer = value

    def run_pipeline(self) -> bool:
        """
        Основной метод запуска пайплайна для юнит-тестов и CI/CD проверки.
        """
        try:
            gateway_result = self.gateway.scan_and_evaluate()
        except Exception:
            gateway_result = {"status": "failed"}

        try:
            analyzer_result = self.analyzer.run()
        except Exception:
            analyzer_result = {"status": "error"}

        if not isinstance(gateway_result, dict):
            gateway_result = {}
        if not isinstance(analyzer_result, dict):
            analyzer_result = {}

        # Прерывание CI/CD при наличии критических угроз в анализаторе
        if analyzer_result.get("critical", False) or analyzer_result.get("risk_score", 0) >= 85:
            return False

        # Прерывание CI/CD при блокировке или непрохождении шлюза безопасности
        if gateway_result.get("status") not in ("clean", "secure_gateway_passed"):
            return False

        if gateway_result.get("risk_score", 0) >= 85:
            return False

        return True

    def process_audit_stream(self, stream):
        """
        Обработка потока данных через анализатор.
        """
        return self.analyzer.process_vulnerability_stream(stream)

    def execute_security_check(self) -> bool:
        """
        Интеграционный метод проверки безопасности.
        """
        return self.run_pipeline()

    def evaluate_risk(self, metrics: dict):
        """
        Оценка риска уязвимостей на основе метрик.
        """
        return self.analyzer.evaluate_risk_score(metrics)


def __getattr__(name: str):
    if name == "RepoSecurityGateway":
        return repo_security_gateway.RepoSecurityGateway
    if name == "VulnerabilityAnalyzer":
        return vulnerability_analyzer.VulnerabilityAnalyzer
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
