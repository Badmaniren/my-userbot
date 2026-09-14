from skills.ai_diagnostic_agent import AutoCorrector
from skills.diagnostic_reporter import DiagnosticReporter


class DiagnosticActionHub:
    def __init__(self):
        self.corrector = AutoCorrector()
        self.reporter = DiagnosticReporter()

    def handle_critical_failure(self, log_path: str, signature: str) -> bool:
        try:
            report_ok = self.reporter.generate_report(log_path, signature)
            if not report_ok:
                return False
            correction_ok = self.corrector.apply_correction(log_path, signature)
            return bool(correction_ok)
        except Exception:
            return False

    def process_stream_action(self, stream_data) -> bool:
        try:
            report_ok = self.reporter.process_stream_aggregation(stream_data)
            correction_ok = self.corrector.process_error_stream(stream_data)
            return bool(report_ok and correction_ok)
        except Exception:
            return False

    def verify_system_and_fix(self, health_url: str) -> bool:
        try:
            report_ok = self.reporter.verify_system_health(health_url)
            correction_ok = self.corrector.verify_fix_via_web(health_url)
            return bool(report_ok and correction_ok)
        except Exception:
            return False

    def run_hub_pipeline(self, log_path: str, signature: str) -> bool:
        try:
            report_ok = self.reporter.generate_report(log_path, signature)
            correction_ok = self.corrector.parse_and_correct_log_file(log_path)
            return bool(report_ok and correction_ok)
        except Exception:
            return False

    def process_action_hub(self, log_path: str) -> bool:
        try:
            report_ok = self.reporter.generate_report(log_path, "default_sig")
            correction_ok = self.corrector.parse_and_correct_log_file(log_path)
            return bool(report_ok and correction_ok)
        except Exception:
            return False