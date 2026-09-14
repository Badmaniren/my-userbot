import unittest
from skills.error_pipeline import ErrorPipeline


class TestErrorPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.pipeline = ErrorPipeline()

    def test_error_pipeline_integration(self):
        stream_data = "ERROR: Test stream error signature"
        stream_result = self.pipeline.process_error_stream(stream_data)
        self.assertIsInstance(stream_result, bool)

        log_file = "test_error.log"
        log_result = self.pipeline.parse_and_correct_log_file(log_file)
        self.assertIsInstance(log_result, bool)

        signature = "NullPointerException: division by zero"
        signature_result = self.pipeline.analyze_and_correct_signature(signature)
        self.assertIsInstance(signature_result, bool)

        process_result = self.pipeline.process_error(signature)
        self.assertIsInstance(process_result, bool)


if __name__ == "__main__":
    unittest.main()
