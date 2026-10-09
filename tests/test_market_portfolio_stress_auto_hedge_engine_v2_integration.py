import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_engine_v2 import (
    market_portfolio_stress_auto_hedge_engine_v2,
    db_storage,
    market_portfolio_scenario_simulator,
    market_portfolio_execution_pipeline,
    market_portfolio_monitor
)

class TestMarketPortfolioStressAutoHedgeEngineV2Integration(unittest.TestCase):
    def test_auto_hedge_engine_real_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(10000.0, 1000000.0), 2)
        stress_drop_pct = round(random.uniform(5.0, 35.0), 2)
        
        sim_result = market_portfolio_scenario_simulator(
            portfolio_id=portfolio_id,
            drop_percentage=stress_drop_pct
        )
        self.assertIsNotNone(sim_result)
        
        hedge_action = market_portfolio_stress_auto_hedge_engine_v2(
            portfolio_id=portfolio_id,
            simulation_data=sim_result,
            capital=initial_capital
        )
        self.assertIsNotNone(hedge_action)
        
        execution_res = market_portfolio_execution_pipeline(
            portfolio_id=portfolio_id,
            order_payload=hedge_action
        )
        self.assertIsNotNone(execution_res)
        
        db_record = db_storage(
            query_type="get_hedge_log",
            portfolio_id=portfolio_id
        )
        self.assertIsNotNone(db_record)
        
        monitor_state = market_portfolio_monitor(portfolio_id=portfolio_id)
        self.assertIsNotNone(monitor_state)

if __name__ == "__main__":
    unittest.main()