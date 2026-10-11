import unittest
import uuid
import random
import os

from skills.market_portfolio_transaction_cost_analyzer import market_portfolio_transaction_cost_analyzer
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer
from skills.market_portfolio_performance_analytics import market_portfolio_performance_analytics

class TestMarketPortfolioTransactionCostAnalyzerIntegration(unittest.TestCase):
    def test_comprehensive_transaction_cost_analysis_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_ticker = f"ASSET_{random.choice(['BTC', 'ETH', 'SOL', 'AAPL', 'TSLA'])}"
        trade_volume = round(random.uniform(1000.0, 500000.0), 2)
        exchange_fee_rate = round(random.uniform(0.0005, 0.003), 4)

        collector_data = market_portfolio_collector_agent(
            portfolio_id=portfolio_id,
            ticker=asset_ticker,
            volume=trade_volume
        )
        self.assertIsNotNone(collector_data)

        slippage_assessment = market_portfolio_slippage_model(
            ticker=asset_ticker,
            volume=trade_volume,
            market_context=collector_data
        )
        self.assertIsNotNone(slippage_assessment)

        liquidity_metrics = market_portfolio_liquidity_scenario_analyzer(
            ticker=asset_ticker,
            slippage_data=slippage_assessment
        )
        self.assertIsNotNone(liquidity_metrics)

        cost_analysis_result = market_portfolio_transaction_cost_analyzer(
            portfolio_id=portfolio_id,
            ticker=asset_ticker,
            volume=trade_volume,
            exchange_fee_rate=exchange_fee_rate,
            slippage_metrics=slippage_assessment,
            liquidity_data=liquidity_metrics
        )

        self.assertIsInstance(cost_analysis_result, dict)
        self.assertIn("total_transaction_cost", cost_analysis_result)
        self.assertIn("impact_on_portfolio_return", cost_analysis_result)

        db_record_id = f"cost_log_{uuid.uuid4().hex}"
        db_storage(
            record_id=db_record_id,
            portfolio_id=portfolio_id,
            payload=cost_analysis_result
        )

        performance_report = market_portfolio_performance_analytics(
            portfolio_id=portfolio_id,
            cost_record_id=db_record_id
        )
        self.assertIsNotNone(performance_report)

        report_filepath = f"reports/transaction_cost_{portfolio_id}.json"
        self.assertTrue(
            os.path.exists(report_filepath) or cost_analysis_result.get("portfolio_id") == portfolio_id,
            "Integration pipeline failed to produce expected transaction cost artifacts."
        )

if __name__ == "__main__":
    unittest.main()