from skills.system_resilience_monitor import SystemResilienceMonitor
from skills.predictive_fault_detector import PredictiveFaultDetector

class ResilienceActionHub:
    def __init__(self):
        self.monitor = SystemResilienceMonitor()
        self.detector = PredictiveFaultDetector()

    def run_closed_loop_healing(self, filepath: str, signature: str) -> bool:
        pipeline_res = self.monitor.run_pipeline(filepath)
        diag_hub = self.detector.DiagnosticActionHub()
        hub_res = diag_hub.handle_critical_failure(signature)
        return bool(pipeline_res and hub_res)

    def process_closed_loop_stream(self, stream_io) -> bool:
        bridge = self.monitor.TelemetryErrorBridge()
        action_hub = self.detector.DiagnosticActionHub()

        bridge_res = bridge.process_telemetry_and_errors(stream_io)
        action_res = action_hub.process_stream_action(stream_io)
        return bool(bridge_res and action_res)

    def verify_and_execute_action(self, url: str, signature: str) -> bool:
        corrector = self.detector.AutoCorrector()
        verified = corrector.verify_fix_via_web(url)
        corrected = corrector.correct_code(signature)
        return bool(verified and corrected)

    def execute_action_hub(self, filepath: str, signature: str):
        pipeline_res = self.monitor.run_pipeline(filepath)
        corrector = self.detector.AutoCorrector()
        correction_res = corrector.correct_code(signature)
        return pipeline_res or correction_res

def execute_action_hub_cycle(url: str) -> bool:
    monitor = SystemResilienceMonitor()
    return bool(monitor.verify_and_heal_system(url))

def evaluate_action_hub_health(url: str) -> bool:
    detector = PredictiveFaultDetector()
    reporter = detector.DiagnosticReporter()
    return bool(reporter.verify_system_health(url))