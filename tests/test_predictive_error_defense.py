import unittest
from unittest.mock import patch
import io
from skills.predictive_error_defense import PredictiveErrorDefense

class TestPredictiveErrorDefense(unittest.TestCase):

    def setUp(self):
        self.defense = PredictiveErrorDefense()

    def test_predictive_error_defense_init(self):
        self.assertIsNotNone(self.defense)

    def test_detect_and_prevent_success(self):
        with patch('skills.predictive_error_detector.PredictiveFaultDetector') as mock_detector, \
             patch('skills.error_pipeline.ErrorPipeline.run_pipeline', return_value=True) as mock_pipeline:
            
            instance = mock_detector.return_value
            result = self.defense.detect_and_prevent("test_log.log")
            self.assertTrue(result)
            mock_pipeline.assert_called_once()

    def test_detect_and_prevent_failure(self):
        with patch('skills.predictive_error_detector.PredictiveFaultDetector') as mock_detector, \
             patch('skills.error_pipeline.ErrorPipeline.run_pipeline', return_value=False) as mock_pipeline:
            
            instance = mock_detector.return_value
            result = self.defense.detect_and_prevent("test_log.log")
            self.assertFalse(result)

    def test_process_stream_defense_success(self):
        stream_data = io.BytesIO(b'error stream content')
        with patch('skills.predictive_error_detector.PredictiveFaultDetector') as mock_detector, \
             patch('skills.error_pipeline.ErrorPipeline.process_stream_pipeline', return_value=True) as mock_stream_pipeline:
            
            result = self.defense.process_stream_defense(stream_data)
            self.assertTrue(result)
            mock_stream_pipeline.assert_called_once()

    def test_process_stream_defense_exception_handling(self):
        stream_data = io.BytesIO(b'malformed stream')
        with patch('skills.error_pipeline.ErrorPipeline.process_stream_pipeline', side_effect=Exception("Pipeline Error")):
            result = self.defense.process_stream_defense(stream_data)
            self.assertFalse(result)

    def test_verify_defense_fix_success(self):
        test_url = "http://localhost:8080/health"
        with patch('skills.error_pipeline.ErrorPipeline.verify_pipeline_fix', return_value=True) as mock_verify:
            result = self.defense.verify_defense_fix(test_url)
            self.assertTrue(result)
            mock_verify.assert_called_once_with(test_url)

    def test_verify_defense_fix_failure(self):
        test_url = "http://localhost:8080/health"
        with patch('skills.error_pipeline.ErrorPipeline.verify_pipeline_fix', return_value=False) as mock_verify:
            result = self.defense.verify_defense_fix(test_url)
            self.assertFalse(result)

    def test_handle_signature_defense(self):
        signature = "ERR_CRITICAL_001"
        with patch('skills.error_pipeline.ErrorPipeline.process_error_stream', return_value=True) as mock_process:
            result = self.defense.handle_signature_defense(signature)
            self.assertTrue(result)
            mock_process.assert_called_once_with(signature)

    def test_handle_signature_defense_raises(self):
        signature = "ERR_CRITICAL_002"
        with patch('skills.error_pipeline.ErrorPipeline.process_error_stream', side_effect=ValueError("Invalid signature")):
            with self.assertRaises(ValueError):
                self.defense.handle_signature_defense(signature)

if __name__ == '__main__':
    unittest.main()