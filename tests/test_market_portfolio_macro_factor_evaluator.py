import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import json
import os
import io

from skills.market_portfolio_macro_factor_evaluator import MacroFactorEvaluator


class TestMacroFactorEvaluator(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.collector_mock = MagicMock()
        self.extractor_mock = MagicMock()
        self.evaluator = MacroFactorEvaluator(
            db_storage=self.db_storage_mock,
            collector=self.collector_mock,
            extractor=self.extractor_mock
        )

    def test_fetch_market_data_success(self):
        random_url = f"https://api.market.data/{uuid.uuid4().hex}"
        random_payload = {
            "inflation": random.uniform(0.01, 0.20),
            "interest": random.uniform(0.01, 0.15),
            "commodity": random.choice(["GOLD", "SILVER", "OIL", "COPPER"])
        }

        with patch('skills.market_portfolio_macro_factor_evaluator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = random_payload
            mock_get.return_value = mock_response

            result = self.evaluator._fetch_market_data(random_url)
            self.assertEqual(result, random_payload)
            mock_get.assert_called_once_with(random_url, timeout=10)

    def test_evaluate_portfolio_not_found(self):
        random_portfolio_id = uuid.uuid4().hex
        self.db_storage_mock.get_portfolio.return_value = None

        with self.assertRaises(ValueError) as ctx:
            self.evaluator.evaluate(random_portfolio_id)

        self.assertEqual(str(ctx.exception), "Portfolio not found")
        self.db_storage_mock.get_portfolio.assert_called_once_with(random_portfolio_id)

    def test_evaluate_success_with_db(self):
        random_portfolio_id = uuid.uuid4().hex
        random_inflation = random.uniform(0.01, 0.10)
        random_interest = random.uniform(0.01, 0.08)
        random_commodity = random.choice(["GOLD", "BRENT", "WHEAT"])

        self.db_storage_mock.get_portfolio.return_value = {"id": random_portfolio_id}

        market_data = {
            'inflation': random_inflation,
            'interest': random_interest,
            'commodity': random_commodity
        }

        with patch.object(self.evaluator, '_fetch_market_data', return_value=market_data) as mock_fetch, \
             patch('skills.market_portfolio_macro_factor_evaluator.os.makedirs') as mock_makedirs, \
             patch('builtins.open', create=True) as mock_open:

            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = self.evaluator.evaluate(random_portfolio_id)

            mock_fetch.assert_called_once()
            self.db_storage_mock.save_report.assert_called_once()

            expected_impact = (random_inflation * 0.5) + (random_interest * 0.3)
            self.assertEqual(result['portfolio_id'], random_portfolio_id)
            self.assertEqual(result['inflation'], random_inflation)
            self.assertEqual(result['interest'], random_interest)
            self.assertEqual(result['commodity'], random_commodity)
            self.assertAlmostEqual(result['impact_score'], expected_impact)
            self.assertIn('report_id', result)
            mock_makedirs.assert_called_once_with("reports", exist_ok=True)
            mock_open.assert_called_once_with(f"reports/macro_{random_portfolio_id}.json", 'w', encoding='utf-8')

    def test_check_macro_anomalies(self):
        random_portfolio_id = uuid.uuid4().hex
        random_threshold = random.uniform(0.1, 0.9)
        random_anomaly_result = {"status": "anomaly_detected", "code": uuid.uuid4().hex}

        with patch('skills.market_portfolio_macro_factor_evaluator.market_anomaly_detector') as mock_detector:
            mock_detector.analyze.return_value = random_anomaly_result

            res = self.evaluator.check_macro_anomalies(random_portfolio_id, random_threshold)

            mock_detector.analyze.assert_called_once_with(random_portfolio_id, random_threshold)
            self.assertEqual(res, random_anomaly_result)

    def test_persist_evaluation_with_db(self):
        random_report_id = uuid.uuid4().hex
        random_score = random.uniform(0.0, 1.0)

        self.evaluator.persist_evaluation(random_report_id, random_score)

        self.db_storage_mock.save_report.assert_called_once_with(random_report_id, random_score)

    def test_persist_evaluation_no_db(self):
        random_report_id = uuid.uuid4().hex
        random_score = random.uniform(0.0, 1.0)
        evaluator_no_db = MacroFactorEvaluator(db_storage=None)

        try:
            evaluator_no_db.persist_evaluation(random_report_id, random_score)
        except Exception as e:
            self.fail(f"persist_evaluation raised Exception unexpectedly: {e}")


if __name__ == '__main__':
    unittest.main()