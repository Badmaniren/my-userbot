import unittest
import uuid
import random
import json
import os
from skills.market_portfolio_transaction_cost_analyzer import (
    start_new,
    market_portfolio_transaction_cost_analyzer
)
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
from skills.db_storage import db_storage

class TestMarketPortfolioTransactionCostAnalyzerIntegration(unittest.TestCase):
    def test_start_new_integration_with_tax_calc(self):
        rand_amount = round(random.uniform(5000.0, 50000.0), 2)
        rand_fee = round(random.uniform(0.0005, 0.005), 4)
        rand_tx_id = uuid.uuid4().hex

        config = {
            "transaction_id": rand_tx_id,
            "amount": rand_amount,
            "fee_rate": rand_fee
        }

        result = start_new(
            config, 
            db_storage=db_storage, 
            market_portfolio_tax_calculator=market_portfolio_tax_calculator
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["transaction_id"], rand_tx_id)
        self.assertAlmostEqual(result["total_cost"], rand_amount * rand_fee)

    def test_analyze_costs_and_export_report_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        ticker = f"TCK_{random.randint(100, 999)}"
        volume = round(random.uniform(10.0, 1000.0), 2)
        price = round(random.uniform(50.0, 500.0), 2)

        slippage_metrics = market_portfolio_slippage_model.calculate(volume, price)
        tax_metrics = market_portfolio_tax_calculator.calculate(volume * price)

        payload = {
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "volume": volume,
            "price": price,
            "slippage_metrics": slippage_metrics,
            "tax_metrics": tax_metrics
        }

        analysis = market_portfolio_transaction_cost_analyzer.analyze_costs(payload)

        self.assertIn("total_cost", analysis)
        self.assertIn("base_cost", analysis)
        self.assertGreater(analysis["total_cost"], 0.0)

        filepath = f"test_report_{uuid.uuid4().hex}.json"
        export_payload = {
            "filepath": filepath,
            "portfolio_id": portfolio_id,
            "analysis": analysis
        }

        try:
            market_portfolio_transaction_cost_analyzer.export_report(export_payload)
            self.assertTrue(os.path.exists(filepath))
            
            with open(filepath, "r") as f:
                loaded_data = json.load(f)
                self.assertEqual(loaded_data["portfolio_id"], portfolio_id)
                self.assertEqual(loaded_data["analysis"]["total_cost"], analysis["total_cost"])
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

if __name__ == "__main__":
    unittest.main()