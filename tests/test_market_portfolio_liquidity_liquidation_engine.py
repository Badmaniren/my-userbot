import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_liquidity_liquidation_engine import LiquidationEngine, market_portfolio_liquidity_liquidation_engine


class TestLiquidationEngineStrict(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.asset_ticker = f"ASSET_{uuid.uuid4().hex[:6].upper()}"
        self.volume = round(random.uniform(10.0, 1000.0), 2)
        self.liquidation_price = round(random.uniform(100.0, 5000.0), 2)
        self.event_id = uuid.uuid4().hex
        self.critical_threshold = round(random.uniform(0.01, 0.5), 2)

    def test_factory_function(self):
        engine = market_portfolio_liquidity_liquidation_engine()
        self.assertIsInstance(engine, LiquidationEngine)

    def test_execute_liquidation_with_custom_slippage(self):
        mock_slippage_model = MagicMock()
        slip_val = round(random.uniform(0.01, 0.2), 4)
        mock_slippage_model.calculate.return_value = slip_val

        engine = LiquidationEngine(slippage_model=mock_slippage_model)
        result = engine.execute_liquidation(self.portfolio_id, self.asset_ticker, self.volume, self.liquidation_price)

        expected_final_price = float(self.liquidation_price) * (1.0 - slip_val)
        self.assertEqual(result['portfolio_id'], self.portfolio_id)
        self.assertEqual(result['asset'], self.asset_ticker)
        self.assertEqual(result['volume'], self.volume)
        self.assertEqual(result['initial_price'], self.liquidation_price)
        self.assertAlmostEqual(result['final_price'], expected_final_price, places=2)
        self.assertEqual(result['slippage'], slip_val)
        mock_slippage_model.calculate.assert_called_once_with(self.asset_ticker, self.volume, self.liquidation_price)

    def test_trigger_emergency_stop_stream(self):
        random_stream_data = f"CRITICAL_DROP_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        with patch('skills.market_portfolio_execution_pipeline.get_stream', return_value=mock_stream):
            engine = LiquidationEngine()
            status = engine.trigger_emergency_stop(self.event_id, self.critical_threshold)

            self.assertTrue(status['success'])
            self.assertEqual(status['event_id'], self.event_id)
            self.assertEqual(status['threshold'], self.critical_threshold)
            self.assertIn(self.event_id, status['stream_data'])

    def test_log_liquidation_event(self):
        log_entry = {
            "log_id": uuid.uuid4().hex,
            "portfolio": self.portfolio_id,
            "status": "FORCE_CLOSED"
        }

        with patch('skills.market_portfolio_audit_log_exporter.export') as mock_export:
            engine = LiquidationEngine()
            engine.log_liquidation_event(log_entry)
            mock_export.assert_called_once_with(log_entry)

    def test_process_insider_signal(self):
        alert_id = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "CRITICAL", "EXTREME"])

        with patch('skills.market_insider_alert_pipeline.dispatch') as mock_dispatch:
            engine = LiquidationEngine()
            engine.process_insider_signal(alert_id, severity)
            mock_dispatch.assert_called_once_with(alert_id=alert_id, level=severity)

    def test_process_liquidation_payload(self):
        shock_multiplier = round(random.uniform(0.05, 0.5), 2)
        initial_valuation = round(random.uniform(1000.0, 100000.0), 2)
        payload = {
            "portfolio_id": self.portfolio_id,
            "target_asset": self.asset_ticker,
            "shock_multiplier": shock_multiplier,
            "valuation_snapshot": {
                "valuation": initial_valuation
            }
        }

        engine = LiquidationEngine()
        res = engine.process_liquidation(payload)

        expected_valuation = initial_valuation * (1 - shock_multiplier)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["target_asset"], self.asset_ticker)
        self.assertAlmostEqual(res["final_valuation"], expected_valuation, places=2)
        self.assertEqual(res["status"], "LIQUIDATED")
        self.assertIsInstance(res["liquidation_id"], str)
        self.assertTrue(len(res["liquidation_id"]) > 0)


if __name__ == '__main__':
    unittest.main()