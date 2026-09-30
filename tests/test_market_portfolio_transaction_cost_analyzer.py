import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from skills.market_portfolio_transaction_cost_analyzer import start_new, MarketPortfolioTransactionCostAnalyzer

class TestMarketPortfolioTransactionCostAnalyzer(unittest.TestCase):

    def test_start_new_invalid_config_raises_value_error(self):
        invalid_config = random.choice([
            uuid.uuid4().hex,
            random.randint(1000, 99999),
            None,
            [random.randint(1, 100), uuid.uuid4().hex]
        ])
        with self.assertRaises(ValueError):
            start_new(invalid_config)

    def test_start_new_generates_default_transaction_id_and_costs(self):
        rand_amount = random.uniform(1000.0, 500000.0)
        rand_fee_rate = random.uniform(0.0001, 0.01)
        config = {
            "amount": rand_amount,
            "fee_rate": rand_fee_rate
        }
        
        result = start_new(config)
        
        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["transaction_id"], str)
        self.assertTrue(len(result["transaction_id"]) > 0)
        self.assertAlmostEqual(result["total_cost"], rand_amount * rand_fee_rate)
        self.assertEqual(result["calculated_spread"], 0.05)

    def test_start_new_uses_provided_transaction_id(self):
        custom_tx_id = uuid.uuid4().hex
        rand_amount = random.uniform(100.0, 10000.0)
        config = {
            "transaction_id": custom_tx_id,
            "amount": rand_amount
        }
        
        result = start_new(config)
        
        self.assertEqual(result["transaction_id"], custom_tx_id)

    def test_start_new_invokes_tax_calculator_if_present(self):
        rand_amount = random.uniform(500.0, 75000.0)
        config = {
            "amount": rand_amount
        }
        
        mock_tax_calc = MagicMock()
        
        result = start_new(config, market_portfolio_tax_calculator=mock_tax_calc)
        
        mock_tax_calc.calculate.assert_called_once_with(rand_amount)
        self.assertEqual(result["status"], "success")

    def test_analyzer_analyze_costs_computes_correctly(self):
        analyzer = MarketPortfolioTransactionCostAnalyzer()
        
        volume = random.uniform(10.0, 1000.0)
        price = random.uniform(50.0, 5000.0)
        slippage_cost = random.uniform(1.0, 50.0)
        tax_amount = random.uniform(0.5, 25.0)
        
        payload = {
            "volume": volume,
            "price": price,
            "slippage_metrics": {"slippage_cost": slippage_cost},
            "tax_metrics": {"tax_amount": tax_amount}
        }
        
        res = analyzer.analyze_costs(payload)
        
        expected_base_cost = (volume * price) * 0.001
        expected_total_cost = expected_base_cost + slippage_cost + tax_amount
        
        self.assertAlmostEqual(res["base_cost"], expected_base_cost)
        self.assertAlmostEqual(res["slippage"], slippage_cost)
        self.assertAlmostEqual(res["tax"], tax_amount)
        self.assertAlmostEqual(res["total_cost"], expected_total_cost)

    def test_analyzer_analyze_costs_saves_audit_record(self):
        analyzer = MarketPortfolioTransactionCostAnalyzer()
        
        portfolio_id = uuid.uuid4().hex
        ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        volume = random.uniform(100.0, 500.0)
        price = random.uniform(10.0, 100.0)
        
        payload = {
            "volume": volume,
            "price": price,
            "portfolio_id": portfolio_id,
            "ticker": ticker
        }
        
        with patch("skills.market_portfolio_transaction_cost_analyzer.db_storage") as mock_db:
            res = analyzer.analyze_costs(payload)
            expected_total = (volume * price) * 0.001 + 10.0 + 5.0
            
            mock_db.save_audit_record.assert_called_once_with(
                portfolio_id,
                {
                    "analyzed_ticker": ticker,
                    "total_cost": expected_total
                }
            )
            self.assertEqual(res["total_cost"], expected_total)

    def test_analyzer_export_report_writes_json(self):
        analyzer = MarketPortfolioTransactionCostAnalyzer()
        filepath = f"/tmp/{uuid.uuid4().hex}.json"
        portfolio_id = uuid.uuid4().hex
        analysis_data = {
            "total_cost": random.uniform(10.0, 1000.0),
            "base_cost": random.uniform(5.0, 500.0)
        }
        
        payload = {
            "filepath": filepath,
            "portfolio_id": portfolio_id,
            "analysis": analysis_data
        }
        
        mock_file = MagicMock()
        with patch("builtins.open", return_value=mock_file) as mock_open:
            with patch("json.dump") as mock_json_dump:
                analyzer.export_report(payload)
                
                mock_open.assert_called_once_with(filepath, "w")
                mock_json_dump.assert_called_once()
                args, _ = mock_json_dump.call_args
                self.assertEqual(args[0]["portfolio_id"], portfolio_id)
                self.assertEqual(args[0]["analysis"], analysis_data)

if __name__ == "__main__":
    unittest.main()