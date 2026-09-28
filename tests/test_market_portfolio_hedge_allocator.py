import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_hedge_allocator import (
    MarketPortfolioHedgeAllocator,
    HedgeAllocationError
)


class TestMarketPortfolioHedgeAllocator(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.tail_risk_analyzer = MagicMock()
        self.allocator = MarketPortfolioHedgeAllocator(
            db_storage=self.db_storage,
            tail_risk_analyzer=self.tail_risk_analyzer
        )

    def test_calculate_hedge_allocation_success(self):
        portfolio_id = str(uuid.uuid4().hex)
        var_value = round(random.uniform(0.01, 0.25), 4)
        cvar_value = round(var_value * random.uniform(1.1, 1.8), 4)

        self.tail_risk_analyzer.compute_metrics.return_value = {
            "var": var_value,
            "cvar": cvar_value
        }

        asset_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        allocation_weight = round(random.uniform(0.05, 0.40), 2)

        self.db_storage.fetch_portfolio_assets.return_value = [
            {"symbol": asset_symbol, "exposure": random.randint(1000, 50000)}
        ]

        result = self.allocator.calculate_and_allocate(portfolio_id)

        self.assertIsInstance(result, dict)
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("allocations", result)
        self.assertTrue(len(result["allocations"]) > 0)

        allocated_asset = result["allocations"][0]
        self.assertIn("asset", allocated_asset)
        self.assertIn("weight", allocated_asset)
        self.tail_risk_analyzer.compute_metrics.assert_called_once_with(portfolio_id)

    def test_calculate_hedge_allocation_failure_on_risk_analyzer(self):
        portfolio_id = str(uuid.uuid4().hex)
        error_msg = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        self.tail_risk_analyzer.compute_metrics.side_effect = Exception(error_msg)

        with self.assertRaises(HedgeAllocationError) as ctx:
            self.allocator.calculate_and_allocate(portfolio_id)

        self.assertIn(error_msg, str(ctx.exception))

    def test_external_parser_integration_with_random_stream(self):
        random_bytes = bytes(''.join(random.choices(string.ascii_letters, k=64)), encoding='utf-8')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = io.BytesIO(random_bytes)

        target_url = f"https://{uuid.uuid4().hex}.com/api/v1/hedge"

        with patch('requests.get', return_value=mock_response) as mock_get:
            response_data = self.allocator.fetch_external_hedge_feed(target_url)
            mock_get.assert_called_once_with(target_url, stream=True)
            self.assertEqual(response_data, random_bytes)

    def test_html_parsing_bs4_anomaly(self):
        random_class = str(uuid.uuid4().hex)
        random_text = str(uuid.uuid4().hex)
        html_content = f'<html><body><div class="{random_class}">{random_text}</div></body></html>'

        soup = BeautifulSoup(html_content, 'html.parser')
        extracted_value = soup.find('div', class_=random_class).text

        self.assertEqual(extracted_value, random_text)

    def test_allocator_weights_sum_normalization(self):
        portfolio_id = str(uuid.uuid4().hex)
        self.tail_risk_analyzer.compute_metrics.return_value = {
            "var": 0.15,
            "cvar": 0.22
        }

        raw_weights = [random.uniform(1.0, 5.0) for _ in range(3)]
        total_weight = sum(raw_weights)
        expected_normalized = [w / total_weight for w in raw_weights]

        with patch.object(self.allocator, '_raw_allocation_generator', return_value=raw_weights):
            normalized = self.allocator.normalize_weights(portfolio_id, raw_weights)

            for actual, expected in zip(normalized, expected_normalized):
                self.assertAlmostEqual(actual, expected, places=5)


if __name__ == '__main__':
    unittest.main()