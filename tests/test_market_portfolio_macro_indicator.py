import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_macro_indicator import (
    get_macro_indicators,
    store_macro_data,
    evaluate_macro_anomaly,
    trigger_macro_alert,
    parse_macro_stream,
    fetch_external_macro_data,
    run_macro_scenario,
    optimize_strategy_based_on_macro,
    create_macro_report,
    evaluate_macro_risk,
    market_portfolio_macro_indicator
)

class TestMarketPortfolioMacroIndicator(unittest.TestCase):

    def setUp(self):
        self.rand_token = uuid.uuid4().hex
        self.rand_payload = {uuid.uuid4().hex: random.randint(1, 100)}
        self.rand_indicator_id = uuid.uuid4().hex
        self.rand_msg = uuid.uuid4().hex
        self.rand_endpoint = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.rand_params = {uuid.uuid4().hex: random.random()}
        self.rand_strategy = uuid.uuid4().hex
        self.rand_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.rand_metrics = {uuid.uuid4().hex: random.random()}
        self.instance = market_portfolio_macro_indicator()

    @patch("skills.market_portfolio_macro_indicator.extractor_tool_1790087207")
    def test_get_macro_indicators(self, mock_extractor):
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_extractor.return_value = expected_result
        res = get_macro_indicators(self.rand_token)
        mock_extractor.assert_called_once_with(self.rand_token)
        self.assertEqual(res, expected_result)

    @patch("skills.market_portfolio_macro_indicator.db_storage")
    def test_store_macro_data(self, mock_db):
        mock_db.save.return_value = True
        res = store_macro_data(self.rand_payload)
        mock_db.save.assert_called_once_with(self.rand_payload)
        self.assertTrue(res)

    @patch("skills.market_portfolio_macro_indicator.market_anomaly_detector")
    def test_evaluate_macro_anomaly(self, mock_detector):
        mock_detector.check_anomaly.return_value = False
        res = evaluate_macro_anomaly(self.rand_indicator_id)
        mock_detector.check_anomaly.assert_called_once_with(self.rand_indicator_id)
        self.assertFalse(res)

    @patch("skills.market_portfolio_macro_indicator.market_portfolio_alert_dispatcher")
    def test_trigger_macro_alert(self, mock_dispatcher):
        mock_dispatcher.dispatch.return_value = None
        trigger_macro_alert(self.rand_msg)
        mock_dispatcher.dispatch.assert_called_once_with(self.rand_msg)

    @patch("skills.market_portfolio_macro_indicator.market_parser")
    def test_parse_macro_stream_with_parser(self, mock_parser):
        expected_parsed = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_parser.parse.return_value = expected_parsed
        mock_stream = MagicMock()
        res = parse_macro_stream(mock_stream)
        mock_parser.parse.assert_called_once_with(mock_stream)
        self.assertEqual(res, expected_parsed)

    def test_parse_macro_stream_fallback(self):
        with patch("skills.market_portfolio_macro_indicator.market_parser", spec=[]) as mock_parser:
            del mock_parser.parse
            rand_bytes = uuid.uuid4().bytes
            mock_stream = io.BytesIO(rand_bytes)
            res = parse_macro_stream(mock_stream)
            self.assertEqual(res, rand_bytes)

    @patch("skills.market_portfolio_macro_indicator.market_portfolio_api_gateway")
    def test_fetch_external_macro_data(self, mock_gateway):
        expected_data = {uuid.uuid4().hex: random.randint(10, 50)}
        mock_gateway.get.return_value = expected_data
        res = fetch_external_macro_data(self.rand_endpoint)
        mock_gateway.get.assert_called_once_with(self.rand_endpoint)
        self.assertEqual(res, expected_data)

    @patch("skills.market_portfolio_macro_indicator.market_portfolio_scenario_simulator")
    def test_run_macro_scenario(self, mock_simulator):
        expected_sim = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_simulator.run_simulation.return_value = expected_sim
        res = run_macro_scenario(self.rand_params)
        mock_simulator.run_simulation.assert_called_once_with(self.rand_params)
        self.assertEqual(res, expected_sim)

    @patch("skills.market_portfolio_macro_indicator.market_portfolio_strategy_optimizer")
    def test_optimize_strategy_based_on_macro(self, mock_optimizer):
        expected_opt = uuid.uuid4().hex
        mock_optimizer.optimize.return_value = expected_opt
        res = optimize_strategy_based_on_macro(self.rand_strategy)
        mock_optimizer.optimize.assert_called_once_with(self.rand_strategy)
        self.assertEqual(res, expected_opt)

    @patch("skills.market_portfolio_macro_indicator.market_report_generator")
    def test_create_macro_report(self, mock_generator):
        expected_report = uuid.uuid4().hex
        mock_generator.generate.return_value = expected_report
        res = create_macro_report(self.rand_data)
        mock_generator.generate.assert_called_once_with(self.rand_data)
        self.assertEqual(res, expected_report)

    @patch("skills.market_portfolio_macro_indicator.market_sentiment_risk_hub")
    def test_evaluate_macro_risk(self, mock_risk_hub):
        expected_risk = {uuid.uuid4().hex: random.random()}
        mock_risk_hub.evaluate.return_value = expected_risk
        res = evaluate_macro_risk(self.rand_metrics)
        mock_risk_hub.evaluate.assert_called_once_with(self.rand_metrics)
        self.assertEqual(res, expected_risk)

    def test_market_portfolio_macro_indicator_process_with_valid_data(self):
        req_id = uuid.uuid4().hex
        inf_val = round(random.uniform(1.0, 10.0), 2)
        gdp_val = round(random.uniform(-3.0, 5.0), 2)
        raw_data = {"inflation": inf_val, "gdp": gdp_val}

        result = self.instance.process_indicators(raw_data, req_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("correlation_id"), req_id)
        self.assertIn("metrics", result)
        self.assertEqual(result["metrics"]["inflation_rate"], inf_val)
        self.assertEqual(result["metrics"]["gdp_growth"], gdp_val)

    def test_market_portfolio_macro_indicator_process_with_invalid_data(self):
        req_id = uuid.uuid4().hex
        invalid_data = uuid.uuid4().hex

        result = self.instance.process_indicators(invalid_data, req_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("correlation_id"), req_id)
        self.assertIn("metrics", result)
        self.assertEqual(result["metrics"]["inflation_rate"], 2.5)
        self.assertEqual(result["metrics"]["gdp_growth"], 1.8)

if __name__ == "__main__":
    unittest.main()