from skills.dependency_scanner import DependencyScanner
from skills.vulnerability_analyzer import VulnerabilityAnalyzer
from skills.repo_reporter import RepoReporter
from skills.repo_logger import RepoLogger


class RepoSecurityGateway:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def start_new(self) -> dict:
        try:
            scanner = DependencyScanner(self.repo_path)
            stream_data = scanner.run()

            analyzer = VulnerabilityAnalyzer(self.repo_path)
            analysis_result = analyzer.run()

            risk_score = analysis_result.get("risk_score", 0)

            if risk_score >= 85:
                logger = RepoLogger(self.repo_path)
                logger.log_error("ERR_HIGH_RISK", f"High vulnerability risk score detected: {risk_score}")
                
                result = {
                    "risk_score": risk_score,
                    "status": "blocked_by_security_gateway"
                }
                if "error_token" in analysis_result:
                    result["error_token"] = analysis_result["error_token"]
                return result

            reporter = RepoReporter(self.repo_path)
            report_path = reporter.generate_report()

            return {
                "risk_score": risk_score,
                "report_path": report_path,
                "status": "secure_gateway_passed"
            }

        except Exception as e:
            logger = RepoLogger(self.repo_path)
            logger.log_error("ERR_GATEWAY", str(e))

            return {
                "status": "failed",
                "error": str(e)
            }

    def run(self) -> dict:
        return self.start_new()

    def scan_and_evaluate(self) -> dict:
        return self.start_new()