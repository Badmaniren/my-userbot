import unittest
from unittest.mock import patch
import random
import uuid
import io
import time
from skills.market_portfolio_macro_liquidity_gate import MacroLiquidityGate, check_macro_liquidity_availability

class TestMarketPortfolioMacroLiquidityGate(unittest.TestCase):
    def test_check_liquidity_success(self):
        rand_endpoint = f"https://{uuid.uuid4().hex}.com/api"
        rand_timeout = random.randint(1, 10)
        rand_liquidity = random.uniform(10.0, 1000.0)
        rand_status = uuid.uuid4().hex

        gate = MacroLiquidityGate(macro_endpoint=rand_endpoint, timeout=rand_timeout)

        mock_response = unittest.mock.Mock()
        mock_response.json.return_value = {
            "liquidity_index": rand_liquidity,
            "status": rand_status
        }
        mock_response.raise_for_status.return_value = None

        with patch("skills.market_portfolio_macro_liquidity_gate.requests.get", return_value=mock_response) as mock_get:
            result = gate.check_liquidity()
            mock_get.assert_called_once_with(rand_endpoint, timeout=rand_timeout)

        self.assertTrue(result["available"])
        self.assertEqual(result["liquidity_index"], rand_liquidity)
        self.assertEqual(result["status"], rand_status)
        self.assertIn("timestamp", result)

    def test_check_liquidity_exception(self):
        rand_endpoint = f"https://{uuid.uuid4().hex}.org/macro"
        rand_timeout = random.randint(1, 10)
        rand_err_msg = uuid.uuid4().hex

        gate = MacroLiquidityGate(macro_endpoint=rand_endpoint, timeout=rand_timeout)

        with patch("skills.market_portfolio_macro_liquidity_gate.requests.get", side_effect=Exception(rand_err_msg)) as mock_get:
            result = gate.check_liquidity()
            mock_get.assert_called_once_with(rand_endpoint, timeout=rand_timeout)

        self.assertFalse(result["available"])
        self.assertEqual(result["liquidity_index"], 0.0)
        self.assertIn(rand_err_msg, result["error"])

    def test_stream_macro_feed(self):
        rand_endpoint = f"https://{uuid.uuid4().hex}.net/stream"
        rand_timeout = random.randint(1, 10)
        rand_bytes = uuid.uuid4().hex.encode('utf-8')

        gate = MacroLiquidityGate(macro_endpoint=rand_endpoint, timeout=rand_timeout)

        mock_response = unittest.mock.Mock()
        mock_response.raw = io.BytesIO(rand_bytes)

        with patch("skills.market_portfolio_macro_liquidity_gate.requests.get", return_value=mock_response) as mock_get:
            data = gate.stream_macro_feed()
            mock_get.assert_called_once_with(rand_endpoint, stream=True, timeout=rand_timeout)

        self.assertEqual(data, rand_bytes)

    def test_check_macro_liquidity_availability(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        payload = {rand_key: rand_val}

        result = check_macro_liquidity_availability(payload)

        self.assertTrue(result["available"])
        self.assertIn("timestamp", result)
        self.assertEqual(result[rand_key], rand_val)