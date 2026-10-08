import unittest
import random
import uuid
from skills.market_insider_hedging_calculator import MarketInsiderHedgingCalculator
from skills.market_insider_anomaly_analyzer import MarketInsiderAnomalyAnalyzer
from skills.market_portfolio_valuation import MarketPortfolioValuation

class TestMarketInsiderHedgingCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.valuation_service = MarketPortfolioValuation()
        self.anomaly_analyzer = MarketInsiderAnomalyAnalyzer()
        self.hedging_calculator = MarketInsiderHedgingCalculator(
            valuation_service=self.valuation_service,
            anomaly_analyzer=self.anomaly_analyzer
        )

    def test_calculate_optimal_hedging_from_raw_portfolio_and_insider_data(self):
        portfolio_id = str(uuid.uuid4())

        # Generate random assets with random prices, quantities, and betas
        asset_1 = f"TICKER_{uuid.uuid4().hex[:4].upper()}"
        asset_2 = f"TICKER_{uuid.uuid4().hex[:4].upper()}"

        price_1 = round(random.uniform(50.0, 250.0), 2)
        qty_1 = random.randint(1000, 5000)
        beta_1 = round(random.uniform(0.8, 1.8), 2)

        price_2 = round(random.uniform(10.0, 100.0), 2)
        qty_2 = random.randint(5000, 20000)
        beta_2 = round(random.uniform(0.5, 1.2), 2)

        portfolio_data = {
            "portfolio_id": portfolio_id,
            "positions": [
                {"asset": asset_1, "quantity": qty_1, "price": price_1, "beta": beta_1},
                {"asset": asset_2, "quantity": qty_2, "price": price_2, "beta": beta_2}
            ]
        }

        # Generate random insider activities indicating potential anomalies
        insider_activities = [
            {
                "asset": asset_1,
                "insider_title": "CEO",
                "transaction_type": "SELL",
                "shares_traded": random.randint(50000, 100000),
                "transaction_value": random.uniform(1000000.0, 5000000.0),
                "days_ago": random.randint(1, 5)
            },
            {
                "asset": asset_2,
                "insider_title": "CFO",
                "transaction_type": "SELL",
                "shares_traded": random.randint(20000, 50000),
                "transaction_value": random.uniform(500000.0, 1500000.0),
                "days_ago": random.randint(1, 3)
            }
        ]

        # Run integration flow
        # 1. Valuation service calculates portfolio metrics
        valuation_results = self.valuation_service.calculate_portfolio_value(portfolio_data)

        # 2. Anomaly analyzer processes raw insider activities
        anomaly_results = self.anomaly_analyzer.analyze_insider_transactions(insider_activities)

        # 3. Hedging calculator computes optimal parameters based on both outputs
        risk_tolerance = round(random.uniform(0.1, 0.5), 2)
        hedging_strategy = self.hedging_calculator.calculate_hedging_strategy(
            portfolio_valuation=valuation_results,
            anomaly_analysis=anomaly_results,
            risk_tolerance=risk_tolerance
        )

        # Assertions to verify integration correctness and dynamic values
        self.assertEqual(hedging_strategy["portfolio_id"], portfolio_id)
        self.assertIn("hedging_positions", hedging_strategy)
        self.assertIn("total_hedging_cost", hedging_strategy)
        self.assertIn("recommended_hedge_ratio", hedging_strategy)

        # Verify that the calculated values are positive and non-trivial
        self.assertGreater(hedging_strategy["total_hedging_cost"], 0)
        self.assertGreater(hedging_strategy["recommended_hedge_ratio"], 0)

        # Verify that the hedging positions correspond to our randomly generated assets
        hedged_assets = [pos["asset"] for pos in hedging_strategy["hedging_positions"]]
        self.assertTrue(any(asset in hedged_assets for asset in [asset_1, asset_2]))

        # Verify mathematical consistency: higher anomaly score should increase hedge ratio
        high_anomaly_activities = [
            {
                "asset": asset_1,
                "insider_title": "CEO",
                "transaction_type": "SELL",
                "shares_traded": random.randint(1000000, 2000000),
                "transaction_value": random.uniform(50000000.0, 100000000.0),
                "days_ago": 1
            }
        ]
        high_anomaly_results = self.anomaly_analyzer.analyze_insider_transactions(high_anomaly_activities)
        high_hedging_strategy = self.hedging_calculator.calculate_hedging_strategy(
            portfolio_valuation=valuation_results,
            anomaly_analysis=high_anomaly_results,
            risk_tolerance=risk_tolerance
        )

        self.assertGreaterEqual(
            high_hedging_strategy["recommended_hedge_ratio"],
            hedging_strategy["recommended_hedge_ratio"]
        )

if __name__ == "__main__":
    unittest.main()