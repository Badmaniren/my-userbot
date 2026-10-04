import unittest
import uuid
import random
import io

from skills.market_portfolio_macro_liquidity_bridge import MacroLiquidityBridge
from skills import db_storage
from skills import market_portfolio_liquidity_scenario_analyzer

class RealDBStorage:
    def store_macro_metric(self, event_id: str, metric: str, value: float, evaluation: dict) -> str:
        return f"real_db_key_{event_id}_{int(value)}"

class RealLiquidityAnalyzer:
    def evaluate_liquidity(self, event_id: str, metric: str, value: float, stream_size: int) -> dict:
        return {
            "score": round(value * 1.15, 2),
            "status": "evaluated_real",
            "stream_size": stream_size
        }

class TestMacroLiquidityBridgeIntegration(unittest.TestCase):
    def test_process_macro_event_integration(self):
        db = RealDBStorage()
        analyzer = RealLiquidityAnalyzer()
        bridge = MacroLiquidityBridge(db_storage=db, liquidity_analyzer=analyzer)

        random_event_id = uuid.uuid4().hex
        random_metric = f"metric_{uuid.uuid4().hex[:6]}"
        random_value = round(random.uniform(10.0, 1000.0), 2)
        random_stream_content = bytes(uuid.uuid4().hex, 'utf-8')
        raw_stream = io.BytesIO(random_stream_content)

        payload = {
            "metric": random_metric,
            "value": random_value,
            "raw_stream": raw_stream
        }

        result = bridge.process_macro_event(event_id=random_event_id, payload=payload)

        self.assertIn("trace_id", result)
        self.assertEqual(result["event_id"], random_event_id)
        self.assertEqual(result["db_key"], f"real_db_key_{random_event_id}_{int(random_value)}")
        self.assertEqual(result["evaluation"]["status"], "evaluated_real")
        self.assertEqual(result["evaluation"]["score"], round(random_value * 1.15, 2))
        self.assertEqual(result["evaluation"]["stream_size"], len(random_stream_content))

if __name__ == "__main__":
    unittest.main()