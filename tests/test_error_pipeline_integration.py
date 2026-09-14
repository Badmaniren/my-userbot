import unittest
from skills.error_pipeline import ErrorPipeline
from skills.error_analyzer import ErrorAnalyzer
from skills.auto_corrector import AutoCorrector

class TestErrorPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.pipeline = ErrorPipeline()
        self.analyzer = ErrorAnalyzer()
        self.corrector = AutoCorrector()

    def test_pipeline_real_integration(self):
        test_signature = "TypeError: unsupported operand type"
        
        analysis_result = self.analyzer.analyze_and_prevent(test_signature)
        self.assertIsInstance(analysis_result, bool)

        correction_result = self.corrector.correct_code(test_signature)
        self.assertIsInstance(correction_result, bool)

        pipeline_result = self.pipeline.process_error_stream(test_signature)
        self.assertIsInstance(pipeline_result, bool)

if __name__ == "__main__":
    unittest.main()