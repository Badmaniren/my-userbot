import unittest
from skills.ai_diagnostic_agent import (
    AutoCorrector,
    ErrorAnalyzer,
    ErrorPipeline,
    SystemTelemetry,
    TelemetryErrorBridge,
    TelemetryOptimizer,
    has_critical_errors,
    analyze_errors,
    save_error_report
)

class TestAIDiagnosticAgentIntegration(unittest.TestCase):
    def setUp(self):
        self.auto_corrector = AutoCorrector()
        self.error_analyzer = ErrorAnalyzer()
        self.error_pipeline = ErrorPipeline()
        self.system_telemetry = SystemTelemetry()
        self.telemetry_bridge = TelemetryErrorBridge()
        self.telemetry_optimizer = TelemetryOptimizer()

    def test_full_diagnostic_and_correction_pipeline(self):
        dummy_log_path = "test_system.log"
        dummy_stream = "ERROR: Critical failure in endpoint /health"
        dummy_url = "http://localhost/health"
        dummy_signature = "CRITICAL_ENDPOINT_FAILURE"

        log_parsed = self.error_analyzer.parse_log(dummy_log_path)
        self.assertIsInstance(log_parsed, bool)

        has_crits = has_critical_errors(dummy_stream)
        self.assertIsInstance(has_crits, bool)

        analysis_result = analyze_errors(dummy_stream)
        self.assertIsInstance(analysis_result, str)

        report_saved = save_error_report(analysis_result)
        self.assertIsInstance(report_saved, bool)

        bridge_processed = self.telemetry_bridge.process_telemetry_and_errors(dummy_stream)
        self.assertIsInstance(bridge_processed, bool)

        pipeline_run = self.error_pipeline.run_pipeline(dummy_log_path)
        self.assertIsInstance(pipeline_run, bool)

        stream_pipe = self.error_pipeline.process_stream_pipeline(dummy_stream)
        self.assertIsInstance(stream_pipe, bool)

        correction_applied = self.auto_corrector.apply_correction(dummy_signature)
        self.assertIsInstance(correction_applied, bool)

        code_corrected = self.auto_corrector.correct_code(dummy_signature)
        self.assertIsInstance(code_corrected, bool)

        fix_verified = self.error_pipeline.verify_pipeline_fix(dummy_url)
        self.assertIsInstance(fix_verified, bool)

        web_verified = self.auto_corrector.verify_fix_via_web(dummy_url)
        self.assertIsInstance(web_verified, bool)

        optimization_run = self.telemetry_optimizer.optimize_pipeline(dummy_log_path)
        self.assertIsInstance(optimization_run, bool)

        opt_stream = self.telemetry_optimizer.process_telemetry_stream(dummy_stream)
        self.assertIsInstance(opt_stream, bool)

        opt_verified = self.telemetry_optimizer.verify_optimization(dummy_url)
        self.assertIsInstance(opt_verified, bool)

if __name__ == "__main__":
    unittest.main()