import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_macro_scenario_adapter import (
    MarketPortfolioMacroScenarioAdapter,
    MacroScenarioAdapterException
)


class TestMarketPortfolioMacroScenarioAdapter(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool_1 = MagicMock()
        self.market_scenario_simulator = MagicMock()

        self.adapter = MarketPortfolioMacroScenarioAdapter(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool_1,
            market_scenario_simulator=self.market_scenario_simulator
        )

    def test_adapt_macro_factors_success(self):
        random_suffix = uuid.uuid4().hex
        macro_indicator = f"gdp_growth_{random_suffix}"
        indicator_value = round(random.uniform(-5.0, 5.0), 4)
        portfolio_id = uuid.uuid4().hex
        expected_scenario_id = uuid.uuid4().hex

        self.extractor_tool_1.fetch_factor.return_value = {
            "indicator": macro_indicator,
            "value": indicator_value
        }
        self.market_scenario_simulator.generate.return_value = {
            "scenario_id": expected_scenario_id,
            "status": "adapted"
        }

        result = self.adapter.adapt_factors(portfolio_id, [macro_indicator])

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("scenario_id"), expected_scenario_id)
        self.market_scenario_simulator.generate.assert_called_once()
        self.db_storage.save_audit_log.assert_called_once()

    def test_adapt_macro_factors_exception_handling(self):
        random_error_msg = ''.join(random.choices(string.ascii_letters, k=16))
        portfolio_id = uuid.uuid4().hex
        macro_indicator = uuid.uuid4().hex

        self.extractor_tool_1.fetch_factor.side_effect = Exception(random_error_msg)

        with self.assertRaises(MacroScenarioAdapterException) as ctx:
            self.adapter.adapt_factors(portfolio_id, [macro_indicator])

        self.assertIn(random_error_msg, str(ctx.exception))
        self.db_storage.save_error_log.assert_called_once()

    def test_stream_parser_integration_with_io(self):
        random_bytes = uuid.uuid4().bytes
        random_tag = ''.join(random.choices(string.ascii_lowercase, k=8))
        html_content = f"<html><body><{random_tag}>{random.randint(100, 999)}</{random_tag}></body></html>"

        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(html_content.encode('utf-8'))
        mock_response.status_code = 200

        with patch('requests.get', return_value=mock_response) as mock_get:
            random_url = f"https://{uuid.uuid4().hex}.org/api/macro"
            parsed_data = self.adapter.parse_external_feed(random_url, random_tag)

            mock_get.assert_called_once_with(random_url, stream=True, timeout=10)
            self.assertIsNotNone(parsed_data)

    def test_randomized_stress_multiplier_logic(self):
        random_portfolio_id = uuid.uuid4().hex
        random_inflation = round(random.uniform(0.1, 15.0), 2)
        random_interest_rate = round(random.uniform(-1.0, 10.0), 2)

        with patch('skills.market_portfolio_macro_scenario_adapter.MarketPortfolioMacroScenarioAdapter._compute_internal_stress') as mock_compute:
            expected_stress_score = round(random.uniform(10.0, 99.9), 2)
            mock_compute.return_value = expected_stress_score

            score = self.adapter.evaluate_macro_stress(
                portfolio_id=random_portfolio_id,
                inflation=random_inflation,
                interest_rate=random_interest_rate
            )

            self.assertEqual(score, expected_stress_score)
            mock_compute.assert_called_once_with(random_portfolio_id, random_inflation, random_interest_rate)


if __name__ == '__main__':
    unittest.main()