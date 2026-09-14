from skills.predictive_error_defense import PredictiveErrorDefense
from skills.diagnostic_action_hub import DiagnosticActionHub


class PredictiveDiagnosticHub:
    def __init__(self):
        self.defense = PredictiveErrorDefense()
        self.diagnostic_hub = DiagnosticActionHub()

    def run_autonomous_center(self, log_path: str, signature: str) -> bool:
        try:
            defense_result = self.defense.detect_and_prevent(log_path)
            if not defense_result:
                return False
            diagnostic_result = self.diagnostic_hub.run_hub_pipeline(log_path, signature)
            return bool(diagnostic_result)
        except Exception:
            return False

    def process_stream_center(self, stream_data) -> bool:
        try:
            defense_result = self.defense.process_stream_defense(stream_data)
            diagnostic_result = self.diagnostic_hub.process_stream_action(stream_data)
            return bool(defense_result and diagnostic_result)
        except Exception:
            return False

    def verify_and_heal_system(self, health_url: str) -> bool:
        try:
            defense_verified = self.defense.verify_defense_fix(health_url)
            if not defense_verified:
                return False
            diagnostic_verified = self.diagnostic_hub.verify_system_and_fix(health_url)
            return bool(diagnostic_verified)
        except Exception:
            return False

    def process_predictive_defense(self, log_path: str) -> bool:
        return self.defense.detect_and_prevent(log_path)

    def process_stream_defense_data(self, stream_data) -> bool:
        return self.defense.process_stream_defense(stream_data)

    def handle_hub_action(self, log_path: str, signature: str) -> bool:
        return self.diagnostic_hub.run_hub_pipeline(log_path, signature)

    def process_hub_stream_action(self, stream_data) -> bool:
        return self.diagnostic_hub.process_stream_action(stream_data)

    def verify_hub_system_health(self, health_url: str) -> bool:
        return self.diagnostic_hub.verify_system_and_fix(health_url)

    def run_comprehensive_hub_pipeline(self, log_path: str, signature: str) -> bool:
        defense_res = self.defense.detect_and_prevent(log_path)
        diagnostic_res = self.diagnostic_hub.run_hub_pipeline(log_path, signature)
        return bool(defense_res and diagnostic_res)