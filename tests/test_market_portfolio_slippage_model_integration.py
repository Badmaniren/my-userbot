import unittest
import uuid
import random
import os
from skills.market_portfolio_slippage_model import MarketPortfolioSlippageModel, OrderExecutionParameters

class TestMarketPortfolioSlippageIntegration(unittest.TestCase):
    def setUp(self):
        self.test_log_file = f"test_logs_{uuid.uuid4().hex}.json"
        
        class MockStorage:
            def __init__(self, filename):
                self.filename = filename
                self.data = {}
            def save_logs(self, sim_id, logs):
                self.data[sim_id] = logs
            def get_logs(self, sim_id):
                return self.data.get(sim_id, [])

        self.storage = MockStorage(self.test_log_file)
        self.model = MarketPortfolioSlippageModel(db_storage=self.storage)

    def tearDown(self):
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_full_execution_cycle_integration(self):
        # Генерация случайных данных
        order_id = str(uuid.uuid4())
        ticker = random.choice(["AAPL", "TSLA", "BTC-USD", "ETH-USD"])
        volume = random.uniform(100, 10000)
        volatility = random.uniform(0.01, 0.5)
        
        # 1. Проверка расчета проскальзывания
        params = OrderExecutionParameters(
            order_id=order_id,
            ticker=ticker,
            volume=volume,
            volatility=volatility
        )
        slippage = self.model.calculate_slippage(params)
        self.assertIsInstance(slippage, float)
        self.assertGreaterEqual(slippage, 0)

        # 2. Проверка симуляции исполнения
        market_context = {
            "adv": random.randint(50000, 500000),
            "volatility": volatility,
            "spread_bps": random.uniform(1.0, 10.0)
        }
        order_data = {
            "order_id": order_id,
            "symbol": ticker,
            "side": "BUY",
            "quantity": volume,
            "price": random.uniform(10, 500)
        }
        
        execution_result = self.model.simulate_order_execution(order_data, market_context)
        
        self.assertEqual(execution_result["order_id"], order_id)
        self.assertEqual(execution_result["status"], "FILLED")
        self.assertIn("realized_cost", execution_result)

        # 3. Проверка персистентности (интеграция с хранилищем)
        sim_id = f"sim_{uuid.uuid4().hex}"
        self.model.persist_execution_logs(sim_id, [execution_result], self.storage)
        
        retrieved_logs = self.model.get_execution_logs(sim_id, self.storage)
        self.assertEqual(len(retrieved_logs), 1)
        self.assertEqual(retrieved_logs[0]["order_id"], order_id)
        self.assertEqual(retrieved_logs[0]["realized_cost"], execution_result["realized_cost"])

    def test_batch_processing_consistency(self):
        batch_size = 5
        orders = []
        contexts = {}
        
        for _ in range(batch_size):
            ticker = f"TICKER_{uuid.uuid4().hex[:4]}"
            orders.append({
                "order_id": str(uuid.uuid4()),
                "symbol": ticker,
                "quantity": random.uniform(10, 100)
            })
            contexts[ticker] = {
                "adv": 100000,
                "volatility": 0.2,
                "spread_bps": 5.0
            }
            
        results = self.model.simulate_batch(orders, contexts)
        self.assertEqual(len(results), batch_size)
        self.assertTrue(all(r["status"] == "FILLED" for r in results))

if __name__ == "__main__":
    unittest.main()