import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import json
import io

import skills.market_portfolio_var_risk_optimizer as target_module

class TestMarketPortfolioVarRiskOptimizer(unittest.TestCase):

    def setUp(self):
        self.rand_portfolio_id = str(uuid.uuid4().hex)
        self.rand_var_threshold = float(round(random.uniform(0.01, 0.1), 4))
        self.rand_asset = f"ASSET_{uuid.uuid4().hex[:6].upper()}"
        self.rand_weight = float(round(random.uniform(0.1, 0.9), 2))
        self.rand_filename = f"report_{uuid.uuid4().hex}.json"

    def test_var_risk_optimizer_initialization(self):
        optimizer_class = getattr(target_module, 'VaRRiskOptimizer', None)
        self.assertIsNotNone(optimizer_class, "VaRRiskOptimizer class not found")
        optimizer = optimizer_class(portfolio_id=self.rand_portfolio_id, threshold=self.rand_var_threshold)
        self.assertEqual(optimizer.portfolio_id, self.rand_portfolio_id)
        self.assertEqual(optimizer.threshold, self.rand_var_threshold)

    def test_monte_carlo_var_calculation(self):
        optimizer_class = getattr(target_module, 'VaRRiskOptimizer', None)
        optimizer = optimizer_class(portfolio_id=self.rand_portfolio_id, threshold=self.rand_var_threshold)

        with patch('skills.db_storage.fetch_historical_prices', create=True, return_value=[100.0, 102.0, 101.0, 103.0, 105.0]):
            var_val = optimizer.calculate_monte_carlo_var(confidence=0.95, simulations=100)
            self.assertIsInstance(var_val, float)
            self.assertGreaterEqual(var_val, 0.0)

    def test_portfolio_weights_adjustment_with_db(self):
        optimizer_class = getattr(target_module, 'VaRRiskOptimizer', None)
        optimizer = optimizer_class(portfolio_id=self.rand_portfolio_id, threshold=self.rand_var_threshold)

        with patch('skills.db_storage.update_asset_weight', create=True, return_value=True) as mock_update:
            result = optimizer.adjust_asset_weight(self.rand_asset, self.rand_weight)
            mock_update.assert_called_once_with(self.rand_portfolio_id, self.rand_asset, self.rand_weight)
            self.assertTrue(result)

    def test_stream_data_processing(self):
        optimizer_class = getattr(target_module, 'VaRRiskOptimizer', None)
        optimizer = optimizer_class(portfolio_id=self.rand_portfolio_id, threshold=self.rand_var_threshold)

        random_bytes = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        stream_mock = io.BytesIO(random_bytes)

        res = optimizer.process_stream_data(stream_mock)
        self.assertEqual(res, random_bytes)

    def test_optimization_loop_trigger(self):
        optimizer_class = getattr(target_module, 'VaRRiskOptimizer', None)
        optimizer = optimizer_class(portfolio_id=self.rand_portfolio_id, threshold=0.0001)

        with patch.object(optimizer, 'calculate_monte_carlo_var', return_value=0.5):
            with patch.object(optimizer, 'adjust_asset_weight') as mock_adjust:
                res = optimizer.optimize_portfolio()
                self.assertTrue(res)
                mock_adjust.assert_called()

    def test_optimize_weights_method(self):
        optimizer_class = getattr(target_module, 'VaRRiskOptimizer', None)
        optimizer = optimizer_class()
        tickers = [f"TICK_{uuid.uuid4().hex[:4].upper()}" for _ in range(3)]
        mc_data = {"var": float(round(random.uniform(0.01, 0.09), 4))}

        with patch('skills.db_storage.save_portfolio_record', create=True) as mock_save:
            output = optimizer.optimize_weights(self.rand_portfolio_id, tickers, mc_data)
            self.assertIn("optimized_weights", output)
            self.assertIn("calculated_var", output)
            self.assertEqual(output["calculated_var"], mc_data["var"])
            mock_save.assert_called_once()

    def test_export_audit_report(self):
        optimizer_class = getattr(target_module, 'VaRRiskOptimizer', None)
        optimizer = optimizer_class(portfolio_id=self.rand_portfolio_id, threshold=self.rand_var_threshold)

        mock_record = {"portfolio_id": self.rand_portfolio_id, "var_metric": 0.04}
        with patch('skills.db_storage.get_portfolio_record', create=True, return_value=mock_record):
            with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
                res = optimizer.export_audit_report(self.rand_portfolio_id, self.rand_filename)
                self.assertTrue(res)
                mock_file.assert_called_once_with(self.rand_filename, "w", encoding="utf-8")

if __name__ == '__main__':
    unittest.main()
