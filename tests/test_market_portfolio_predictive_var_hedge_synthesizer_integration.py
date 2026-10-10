import unittest
import uuid
import random
import os
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync
from skills.market_portfolio_predictive_var_hedge_synthesizer import MarketPortfolioPredictiveVarHedgeSynthesizer

class TestMarketPortfolioPredictiveVarHedgeSynthesizerIntegration(unittest.TestCase):
    def test_predictive_var_hedge_synthesizer_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_code = f"scen_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        symbol = random.choice(["BTC", "ETH", "SBER", "GAZP", "AAPL"])
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        percentage = round(random.uniform(1.0, 25.0), 2)
        
        db_storage = f"test_db_{uuid.uuid4().hex[:6]}.db"
        storage_file = f"test_storage_{uuid.uuid4().hex[:6]}.json"

        var_engine = PredictiveVarEngine(
            db_storage=db_storage,
            extractor_tool=None,
            market_anomaly_detector=None
        )
        
        auto_hedge_sync = MarketPortfolioStressAutoHedgeSync(
            db_storage=db_storage,
            monitor=None,
            evaluator=None,
            rebalancer=None,
            storage_file=storage_file,
            advisor=None,
            pipeline=None
        )

        synthesizer = MarketPortfolioPredictiveVarHedgeSynthesizer(
            var_engine=var_engine,
            auto_hedge_sync=auto_hedge_sync
        )

        self.assertTrue(hasattr(synthesizer, "synthesize_and_simulate"))

        simulation_result = synthesizer.synthesize_and_simulate(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            portfolio_value=portfolio_value,
            simulations=100,
            horizon_days=30,
            confidence_level=0.95,
            scenario_params={"volatility_multiplier": 1.5},
            iterations=50,
            shifts={"price_shift": -0.1}
        )

        self.assertIsNotNone(simulation_result)
        self.assertIn("portfolio_id", simulation_result)
        self.assertEqual(simulation_result["portfolio_id"], portfolio_id)
        self.assertIn("hedge_status", simulation_result)

        if os.path.exists(db_storage):
            os.remove(db_storage)
        if os.path.exists(storage_file):
            os.remove(storage_file)

if __name__ == "__main__":
    unittest.main()