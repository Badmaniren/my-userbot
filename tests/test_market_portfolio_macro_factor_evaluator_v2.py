import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests
from skills.market_portfolio_macro_factor_evaluator_v2 import (
    MarketPortfolioMacroFactorEvaluatorV2,
    MacroFactorEvaluationError
)

class TestMarketPortfolioMacroFactorEvaluatorV2(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.evaluator = MarketPortfolioMacroFactorEvaluatorV2(
            db_storage=self.db_storage_mock,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2
        )

    def test_evaluate_macro_factors_success(self):
        portfolio_id = str(uuid.uuid4())
        factor_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        factor_value = random.uniform(-100.0, 100.0)

        self.extractor_1.fetch_factor.return_value = {factor_name: factor_value}
        self.extractor_2.calculate_impact.return_value = factor_value * 1.5

        result = self.evaluator.evaluate_portfolio(portfolio_id, [factor_name])

        self.assertIn(portfolio_id, result.values() or [portfolio_id])
        self.assertIsInstance(result, dict)
        self.db_storage_mock.save_evaluation.assert_called_once()

    def test_evaluate_macro_factors_handles_exception_robustly(self):
        portfolio_id = str(uuid.uuid4())
        bad_factor = ''.join(random.choices(string.ascii_uppercase, k=8))

        self.extractor_1.fetch_factor.side_effect = requests.RequestException(
            f"Network error on {uuid.uuid4().hex}"
        )

        with self.assertRaises(MacroFactorEvaluationError) as ctx:
            self.evaluator.evaluate_portfolio(portfolio_id, [bad_factor])

        self.assertIn(portfolio_id, str(ctx.exception))
        self.db_storage_mock.log_error.assert_called_once()

    def test_stream_data_processing_with_bytes_io(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.printable, k=50)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        with patch('skills.market_portfolio_macro_factor_evaluator_v2.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = mock_stream
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            url = f"https://{uuid.uuid4().hex}.com/api/v2/stream"
            result = self.evaluator.process_stream_feed(url)

            self.assertTrue(result)
            mock_get.assert_called_once_with(url, stream=True)

    def test_anomaly_detection_integration(self):
        anomaly_score = random.uniform(0.0, 1.0)
        portfolio_id = uuid.uuid4().hex

        with patch('skills.market_portfolio_macro_factor_evaluator_v2.market_anomaly_detector') as mock_detector:
            mock_detector.analyze.return_value = {"score": anomaly_score, "id": portfolio_id}

            analysis = self.evaluator.check_anomalies(portfolio_id)

            self.assertEqual(analysis["score"], anomaly_score)
            self.assertEqual(analysis["id"], portfolio_id)
            mock_detector.analyze.assert_called_once_with(portfolio_id)

if __name__ == '__main__':
    unittest.main()