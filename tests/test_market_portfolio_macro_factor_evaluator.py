import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.market_portfolio_macro_factor_evaluator import MarketPortfolioMacroFactorEvaluator


class TestMarketPortfolioMacroFactorEvaluator(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.extractor_4 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.liquidity_analyzer = MagicMock()
        self.scenario_simulator = MagicMock()
        
        self.evaluator = MarketPortfolioMacroFactorEvaluator(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            extractor_tool_1790621808=self.extractor_4,
            market_anomaly_detector=self.anomaly_detector,
            market_portfolio_liquidity_scenario_analyzer=self.liquidity_analyzer,
            market_portfolio_scenario_simulator=self.scenario_simulator
        )

    def test_evaluate_macro_factors_success(self):
        portfolio_id = str(uuid.uuid4())
        macro_indicator_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        expected_risk_score = round(random.uniform(1.0, 100.0), 2)
        random_bytes = uuid.uuid4().bytes

        mock_response_data = {
            "portfolio_id": portfolio_id,
            "indicator": macro_indicator_name,
            "risk_score": expected_risk_score,
            "status": "evaluated"
        }

        self.db_storage.fetch_portfolio.return_value = {"id": portfolio_id, "assets": [str(uuid.uuid4())]}
        self.extractor_1.extract.return_value = {macro_indicator_name: random.uniform(0, 1)}
        self.anomaly_detector.analyze.return_value = {"anomaly": False}
        self.liquidity_analyzer.evaluate.return_value = {"liquidity_index": random.uniform(10, 50)}

        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_resp.raw = io.BytesIO(random_bytes)
            mock_get.return_value = mock_resp

            result = self.evaluator.evaluate_macro_factors(portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), portfolio_id)
            self.assertEqual(result.get("risk_score"), expected_risk_score)
            self.db_storage.fetch_portfolio.assert_called_once_with(portfolio_id)
            mock_get.assert_called_once()

    def test_evaluate_macro_factors_with_anomaly_trigger(self):
        portfolio_id = str(uuid.uuid4())
        anomaly_code = uuid.uuid4().hex[:8]
        random_text = ''.join(random.choices(string.ascii_uppercase, k=15))

        self.db_storage.fetch_portfolio.return_value = {"id": portfolio_id, "assets": []}
        self.anomaly_detector.analyze.return_value = {"anomaly": True, "code": anomaly_code, "msg": random_text}

        with patch('bs4.BeautifulSoup') as mock_bs:
            mock_soup = MagicMock()
            mock_soup.text = random_text
            mock_bs.return_value = mock_soup

            result = self.evaluator.evaluate_macro_factors(portfolio_id)

            self.assertIn("anomaly_alert", result)
            self.assertTrue(result["anomaly_alert"]["active"])
            self.assertEqual(result["anomaly_alert"]["code"], anomaly_code)
            self.anomaly_detector.analyze.assert_called_once()

    def test_evaluate_macro_factors_database_failure(self):
        portfolio_id = str(uuid.uuid4())
        db_error_message = ''.join(random.choices(string.ascii_letters + string.digits, k=20))

        self.db_storage.fetch_portfolio.side_effect = Exception(db_error_message)

        with self.assertRaises(Exception) as context:
            self.evaluator.evaluate_macro_factors(portfolio_id)

        self.assertIn(db_error_message, str(context.exception))
        self.db_storage.fetch_portfolio.assert_called_once_with(portfolio_id)

    def test_stress_scenario_linkage(self):
        portfolio_id = str(uuid.uuid4())
        scenario_id = str(uuid.uuid4())
        stress_factor = random.choice([1.5, 2.0, 2.5, 3.0])

        self.scenario_simulator.run_simulation.return_value = {
            "scenario_id": scenario_id,
            "portfolio_id": portfolio_id,
            "stress_multiplier": stress_factor,
            "passed": False
        }

        result = self.evaluator.link_stress_scenario(portfolio_id, scenario_id)

        self.assertEqual(result["scenario_id"], scenario_id)
        self.assertEqual(result["stress_multiplier"], stress_factor)
        self.assertFalse(result["passed"])
        self.scenario_simulator.run_simulation.assert_called_once_with(portfolio_id, scenario_id)