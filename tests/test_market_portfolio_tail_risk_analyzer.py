import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import requests
from skills.market_portfolio_tail_risk_analyzer import MarketPortfolioTailRiskAnalyzer, market_portfolio_tail_risk_analyzer

class TestMarketPortfolioTailRiskAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.asset_symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.metric_id = str(uuid.uuid4())
        self.analyzer = MarketPortfolioTailRiskAnalyzer()

    def test_compute_raw_metrics_basic(self):
        count = random.randint(10, 30)
        returns = [random.uniform(-0.05, 0.05) for _ in range(count)]
        confidence = round(random.uniform(0.90, 0.99), 2)
        metrics = self.analyzer.compute_raw_metrics(returns, confidence_level=confidence)
        self.assertIn("var", metrics)
        self.assertIn("cvar", metrics)
        self.assertIsInstance(metrics["var"], float)
        self.assertIsInstance(metrics["cvar"], float)
        self.assertLessEqual(metrics["cvar"], metrics["var"])

    def test_compute_raw_metrics_empty(self):
        metrics = self.analyzer.compute_raw_metrics([], confidence_level=0.95)
        self.assertEqual(metrics["var"], 0.0)
        self.assertEqual(metrics["cvar"], 0.0)

    def test_compute_raw_metrics_positive_var_correction(self):
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]
        metrics = self.analyzer.compute_raw_metrics(returns, confidence_level=0.5)
        self.assertLessEqual(metrics["var"], 0.0)
        self.assertLessEqual(metrics["cvar"], metrics["var"])

    @patch('skills.market_portfolio_tail_risk_analyzer.requests.get')
    def test_fetch_market_stream_success_raw(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        rand_val = random.uniform(-0.1, 0.1)
        mock_response.raw = io.BytesIO(f"[{rand_val}]".encode('utf-8'))
        mock_response.text = ""
        mock_get.return_value = mock_response

        res = self.analyzer._fetch_market_stream(self.portfolio_id)
        self.assertIsInstance(res, list)
        self.assertIn(rand_val, res)

    @patch('skills.market_portfolio_tail_risk_analyzer.requests.get')
    def test_fetch_market_stream_success_text(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = None
        rand_val = random.uniform(-0.1, 0.1)
        mock_response.text = f"[{rand_val}]"
        mock_get.return_value = mock_response

        res = self.analyzer._fetch_market_stream(self.portfolio_id)
        self.assertIsInstance(res, list)
        self.assertIn(rand_val, res)

    @patch('skills.market_portfolio_tail_risk_analyzer.requests.get')
    def test_fetch_market_stream_invalid_eval_fallback(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = None
        mock_response.text = "INVALID_SYNTAX_DATA_XYZ"
        mock_get.return_value = mock_response

        res = self.analyzer._fetch_market_stream(self.portfolio_id)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 50)

    @patch('skills.market_portfolio_tail_risk_analyzer.requests.get')
    def test_fetch_market_stream_non_200(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = random.choice([400, 404, 500, 503])
        mock_get.return_value = mock_response

        res = self.analyzer._fetch_market_stream(self.portfolio_id)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 50)

    @patch('skills.market_portfolio_tail_risk_analyzer.requests.get')
    def test_calculate_tail_risk(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "[0.01, -0.02, -0.03, -0.04]"
        mock_get.return_value = mock_response

        res = self.analyzer.calculate_tail_risk(self.portfolio_id, confidence_level=0.75)
        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var", res)
        self.assertIn("cvar", res)

    def test_evaluate_anomaly_impact_with_detector(self):
        mock_detector = MagicMock()
        sig = str(uuid.uuid4())
        mock_detector.detect.return_value = {
            'signature': sig,
            'asset': self.asset_symbol,
            'is_tail_risk_event': True
        }
        analyzer = MarketPortfolioTailRiskAnalyzer(market_anomaly_detector=mock_detector)
        res = analyzer.evaluate_anomaly_impact(self.asset_symbol)
        self.assertEqual(res['anomaly_signature'], sig)
        self.assertEqual(res['asset'], self.asset_symbol)
        self.assertTrue(res['mitigation_required'])

    def test_evaluate_anomaly_impact_without_detector(self):
        analyzer = MarketPortfolioTailRiskAnalyzer(market_anomaly_detector=None)
        res = analyzer.evaluate_anomaly_impact(self.asset_symbol)
        self.assertEqual(res['asset'], self.asset_symbol)
        self.assertEqual(res['anomaly_signature'], 'default_sig')
        self.assertTrue(res['mitigation_required'])

    def test_persist_tail_risk_metrics_with_db(self):
        mock_db = MagicMock()
        analyzer = MarketPortfolioTailRiskAnalyzer(db_storage=mock_db)
        res_id = analyzer.persist_tail_risk_metrics(self.metric_id)
        self.assertEqual(res_id, self.metric_id)
        mock_db.save_metric.assert_called_once()
        args = mock_db.save_metric.call_args[0]
        self.assertEqual(args[0], self.metric_id)
        self.assertIn("var", args[1])

    def test_persist_tail_risk_metrics_without_db(self):
        analyzer = MarketPortfolioTailRiskAnalyzer(db_storage=None)
        res_id = analyzer.persist_tail_risk_metrics(self.metric_id)
        self.assertEqual(res_id, self.metric_id)

    def test_robust_data_extraction_success(self):
        ext1 = MagicMock()
        ext1.extract.return_value = None
        ext2 = MagicMock()
        expected_data = [random.uniform(-1, 1) for _ in range(5)]
        ext2.extract.return_value = expected_data

        analyzer = MarketPortfolioTailRiskAnalyzer(
            extractor_tool_1790087207=ext1,
            extractor_tool_1790102839=ext2
        )
        res = analyzer.robust_data_extraction(self.portfolio_id)
        self.assertEqual(res, expected_data)

    def test_robust_data_extraction_all_none(self):
        analyzer = MarketPortfolioTailRiskAnalyzer()
        res = analyzer.robust_data_extraction(self.portfolio_id)
        self.assertIsNone(res)

    def test_robust_data_extraction_raises(self):
        ext1 = MagicMock()
        ext1.extract.side_effect = RuntimeError("Extraction failure")
        analyzer = MarketPortfolioTailRiskAnalyzer(extractor_tool_1790087207=ext1)
        with self.assertRaises(RuntimeError):
            analyzer.robust_data_extraction(self.portfolio_id)

    def test_simulate_extreme_shock(self):
        vector = [random.uniform(10, 100) for _ in range(4)]
        shock = random.uniform(1, 10)
        shocked = self.analyzer.simulate_extreme_shock(vector, shock)
        self.assertEqual(len(shocked), len(vector))
        for original, modified in zip(vector, shocked):
            self.assertLess(modified, original)

    @patch('skills.market_portfolio_tail_risk_analyzer._global_analyzer_instance')
    def test_market_portfolio_tail_risk_analyzer_wrapper(self, mock_instance):
        expected_dict = {"var": random.random(), "cvar": random.random(), "portfolio_id": self.portfolio_id}
        mock_instance.calculate_tail_risk.return_value = expected_dict
        res = market_portfolio_tail_risk_analyzer(self.portfolio_id, confidence_level=0.95)
        self.assertEqual(res, expected_dict)
        mock_instance.calculate_tail_risk.assert_called_once_with(self.portfolio_id, 0.95)