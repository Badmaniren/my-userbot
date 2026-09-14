from skills.ai_diagnostic_agent import ErrorAnalyzer, AutoCorrector, save_error_report
from skills.error_pipeline import ErrorPipeline


class DiagnosticReporter:
    def __init__(self):
        self.error_analyzer = ErrorAnalyzer()
        self.auto_corrector = AutoCorrector()
        self.error_pipeline = ErrorPipeline()

    def generate_report(self, log_path, stream_data=None) -> bool:
        try:
            parse_result = self.error_analyzer.parse_log(log_path)
            if not parse_result:
                return False

            pipeline_result = self.error_pipeline.run_pipeline(log_path)
            if not pipeline_result:
                return False

            save_result = save_error_report(log_path)
            return bool(save_result)
        except Exception:
            raise

    def process_stream_aggregation(self, stream_data) -> bool:
        try:
            stream_pipe_result = self.error_pipeline.process_stream_pipeline(stream_data)
            auto_stream_result = self.auto_corrector.process_error_stream(stream_data)
            return bool(stream_pipe_result and auto_stream_result)
        except Exception:
            return False

    def verify_system_health(self, url) -> bool:
        try:
            verify_result = self.error_pipeline.verify_pipeline_fix(url)
            return bool(verify_result)
        except Exception:
            raise