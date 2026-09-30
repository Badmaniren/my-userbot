import unittest
import uuid
import random
import os
from skills.market_portfolio_transaction_cost_analyzer import market_portfolio_transaction_cost_analyzer
from skills.db_storage import db_storage
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator

class TestMarketPortfolioTransactionCostAnalyzerIntegration(unittest.TestCase):

    def test_transaction_cost_analyzer_real_pipeline(self):
        portfolio_id = str(uuid.uuid4())
        asset_ticker = f"TEST_{random.randint(1000, 9999)}"
        trade_volume = round(random.uniform(1000.0, 500000.0), 2)
        execution_price = round(random.uniform(10.0, 1500.0), 2)
        
        db_storage.save_portfolio_record({
            "portfolio_id": portfolio_id,
            "ticker": asset_ticker,
            "initial_capital": trade_volume * 2
        })

        slippage_data = market_portfolio_slippage_model.calculate_slippage({
            "ticker": asset_ticker,
            "volume": trade_volume,
            "price": execution_price
        })

        tax_data = market_portfolio_tax_calculator.compute_projected_tax({
            "portfolio_id": portfolio_id,
            "realized_gain": trade_volume * 0.05
        })

        analysis_result = market_portfolio_transaction_cost_analyzer.analyze_costs({
            "portfolio_id": portfolio_id,
            "ticker": asset_ticker,
            "volume": trade_volume,
            "price": execution_price,
            "slippage_metrics": slippage_data,
            "tax_metrics": tax_data
        })

        self.assertIsInstance(analysis_result, dict)
        self.assertIn("total_cost", analysis_result)
        self.assertGreater(analysis_result["total_cost"], 0.0)

        persisted_audit = db_storage.get_audit_record(portfolio_id)
        self.assertIsNotNone(persisted_audit)
        self.assertEqual(persisted_audit.get("analyzed_ticker"), asset_ticker)

        report_file_path = f"transaction_report_{portfolio_id}.json"
        if os.path.exists(report_file_path):
            os.remove(report_file_path)

        market_portfolio_transaction_cost_analyzer.export_report({
            "portfolio_id": portfolio_id,
            "analysis": analysis_result,
            "filepath": report_file_path
        })

        self.assertTrue(os.path.exists(report_file_path))
        if os.path.exists(report_file_path):
            os.remove(report_file_path)

if __name__ == "__main__":
    unittest.main()