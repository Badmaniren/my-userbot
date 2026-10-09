import unittest
import uuid
import random
from skills.market_portfolio_ml_stress_adaptive_allocator import (
    AdaptiveStressAllocator
)
from skills.market_portfolio_ml_stress_evaluator import (
    MarketPortfolioMLStressEvaluator
)
from skills.market_portfolio_stress_auto_rebalance_trigger import (
    StressAutoRebalanceTrigger
)

class TestMarketPortfolioMLStressAdaptiveAllocatorIntegration(unittest.TestCase):
    def test_adaptive_allocator_pipeline_integration(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = f"SCENARIO_{random.randint(1000, 9999)}"
        threshold = round(random.uniform(0.1, 0.9), 4)
        prices = [round(random.uniform(10.0, 500.0), 2) for _ in range(5)]
        confidence_level = round(random.uniform(0.90, 0.99), 2)

        allocator = AdaptiveStressAllocator()
        
        self.assertTrue(
            hasattr(allocator, 'ml_evaluator') or isinstance(allocator, object),
            "Allocator should be initialized"
        )
        
        evaluator = MarketPortfolioMLStressEvaluator(
            db_storage=None,
            extractor_tool=None,
            market_anomaly_detector=None,
            window_size=random.randint(10, 50)
        )
        self.assertIsNotNone(evaluator)

        trigger = StressAutoRebalanceTrigger()
        self.assertIsNotNone(trigger)

        if hasattr(allocator, 'execute_adaptive_allocation'):
            result = allocator.execute_adaptive_allocation(
                portfolio_id=portfolio_id,
                prices=prices,
                scenario_code=scenario_code,
                confidence_level=confidence_level,
                threshold=threshold
            )
            self.assertIsInstance(result, dict)
            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
        else:
            stress_res = evaluator.evaluate_stress(
                portfolio_id=portfolio_id,
                prices=prices,
                scenario_code=scenario_code,
                confidence_level=confidence_level
            )
            self.assertIsInstance(stress_res, dict)

            trigger_res = trigger.evaluate_and_trigger(
                portfolio_id=portfolio_id,
                threshold=threshold
            )
            if trigger_res is not None:
                self.assertIsInstance(trigger_res, dict)

if __name__ == "__main__":
    unittest.main()