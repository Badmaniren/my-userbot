import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests
import bs4

from skills.market_portfolio_macro_liquidity_gateway import (
    MarketPortfolioMacroLiquidityGateway,
    MacroLiquidityGatewayError
)

class TestMarketPortfolioMacroLiquidityGateway(unittest.TestCase):

    def setUp(self):
        self.gateway = MarketPortfolioMacroLiquidityGateway()

    def test_aggregate_macro_liquidity_success(self):
        rand_endpoint = f"https://{uuid.uuid4().hex}.com/api/{uuid.uuid4().hex}"
        rand_metric_id = str(random.randint(100000, 999999))
        rand_float_val = round(random.uniform(10.5, 999.9), 4)
        rand_string_tag = ''.join(random.choices(string.ascii_letters, k=8))

        mock_payload = {
            "status": "success",
            "metric_id": rand_metric_id,
            "liquidity_value": rand_float_val,
            "tag": rand_string_tag
        }

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_payload
            mock_get.return_value = mock_response

            result = self.gateway.aggregate_and_transfer_liquidity(rand_endpoint)

            mock_get.assert_called_once_with(rand_endpoint, timeout=10)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["metric_id"], rand_metric_id)
            self.assertEqual(result["liquidity_value"], rand_float_val)
            self.assertEqual(result["tag"], rand_string_tag)

    def test_aggregate_macro_liquidity_http_error(self):
        rand_endpoint = f"https://{uuid.uuid4().hex}.org/{uuid.uuid4().hex}"

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
            mock_get.return_value = mock_response

            with self.assertRaises(MacroLiquidityGatewayError):
                self.gateway.aggregate_and_transfer_liquidity(rand_endpoint)

    def test_parse_html_liquidity_indicators_with_soup(self):
        rand_class_name = f"macro-{uuid.uuid4().hex[:6]}"
        rand_numeric_text = f"{random.randint(1000, 99999)}.#{random.randint(10, 99)}"
        rand_html_content = f"<html><body><div class='{rand_class_name}'>{rand_numeric_text}</div></body></html>"

        fake_file_stream = io.BytesIO(rand_html_content.encode('utf-8'))

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = fake_file_stream.read()
            mock_get.return_value = mock_response

            rand_url = f"http://{uuid.uuid4().hex}.net/feed"
            parsed_value = self.gateway.extract_liquidity_from_html(rand_url, rand_class_name)

            self.assertEqual(parsed_value, rand_numeric_text)

    def test_pipeline_routing_and_event_dispatch(self):
        rand_event_id = uuid.uuid4().hex
        rand_scenario_target = f"scenario_{uuid.uuid4().hex[:8]}"
        rand_volume = random.randint(500000, 9999999)

        input_data = {
            "event_id": rand_event_id,
            "target": rand_scenario_target,
            "volume": rand_volume
        }

        with patch.object(self.gateway, '_dispatch_to_scenario_contour', return_value=True) as mock_dispatch:
            status = self.gateway.route_liquidity_to_scenario(input_data)

            mock_dispatch.assert_called_once_with(input_data)
            self.assertTrue(status)

    def test_gateway_exception_handling_on_invalid_json(self):
        rand_endpoint = f"http://{uuid.uuid4().hex}.io/api"

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON payload")
            mock_get.return_value = mock_response

            with self.assertRaises(MacroLiquidityGatewayError):
                self.gateway.aggregate_and_transfer_liquidity(rand_endpoint)

if __name__ == '__main__':
    unittest.main()