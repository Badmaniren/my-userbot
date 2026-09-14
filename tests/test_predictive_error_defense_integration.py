import unittest
from skills.predictive_error_defense import PredictiveErrorDefense

class TestPredictiveErrorDefenseIntegration(unittest.TestCase):
    def setUp(self):
        self.defense_module = PredictiveErrorDefense()

    def test_defense_workflow(self):
        test_log_path = "test_system.log"
        test_signature = "CRITICAL_ANOMALY_SIG"
        test_stream = {"metric": "cpu_load", "value": 99.9}
        test_url = "http://localhost:8080/health"

        has_detector = hasattr(self.defense_module, 'detector') or hasattr(self.defense_module, 'predictive_fault_detector')
        has_pipeline = hasattr(self.defense_module, 'pipeline') or hasattr(self.defense_module, 'error_pipeline')
        
        self.assertTrue(has_detector or has_pipeline, "Модуль должен использовать предиктивный детектор или пайплайн ошибок")

        if hasattr(self.defense_module, 'run_defense_pipeline'):
            result = self.defense_module.run_defense_pipeline(test_log_path, test_signature)
            self.assertIsInstance(result, bool)

        if hasattr(self.defense_module, 'process_defense_stream'):
            stream_result = self.defense_module.process_defense_stream(test_stream)
            self.assertIsInstance(stream_result, bool)

        if hasattr(self.defense_module, 'verify_defense_fix'):
            verify_result = self.defense_module.verify_defense_fix(test_url)
            self.assertIsInstance(verify_result, bool)

if __name__ == "__main__":
    unittest.main()