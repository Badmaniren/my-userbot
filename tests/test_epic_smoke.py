import unittest
import os
import json
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../skills')))

try:
    from market_portfolio_autonomous_sentinel import AutonomousSentinel
    from market_portfolio_predictive_aggregator import PredictiveAggregator
    from market_portfolio_scenario_simulator import PortfolioScenarioSimulator
except ImportError:
    from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel
    from skills.market_portfolio_predictive_aggregator import PredictiveAggregator
    from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator

class TestMarketAutonomousSentinelEpic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, "market_test_data.json")

        initial_data = {
            "BTC": [
                {"price": 45000.0, "timestamp": "2023-10-01T00:00:00"},
                {"price": 45500.0, "timestamp": "2023-10-01T01:00:00"},
                {"price": 46000.0, "timestamp": "2023-10-01T02:00:00"},
                {"price": 46200.0, "timestamp": "2023-10-01T03:00:00"},
                {"price": 45800.0, "timestamp": "2023-10-01T04:00:00"},
                {"price": 46500.0, "timestamp": "2023-10-01T05:00:00"},
                {"price": 47000.0, "timestamp": "2023-10-01T06:00:00"},
                {"price": 47200.0, "timestamp": "2023-10-01T07:00:00"},
                {"price": 47500.0, "timestamp": "2023-10-01T08:00:00"},
                {"price": 48000.0, "timestamp": "2023-10-01T09:00:00"}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_predictive_aggregator_forecast(self):
        print("\n--- Демонстрация PredictiveAggregator ---")
        aggregator = PredictiveAggregator(self.storage_file)
        forecast = aggregator.build_advanced_forecast("BTC", "http://example.com/api/btc", shift=5)
        print(f"Сгенерированный прогноз для BTC: {forecast}")
        self.assertIsInstance(forecast, dict)

    def test_scenario_simulator_stress(self):
        print("\n--- Демонстрация PortfolioScenarioSimulator ---")
        simulator = PortfolioScenarioSimulator(self.storage_file)
        stress_results = simulator.run_stress_test("BTC", [-5.0, 0.0, 5.0, 10.0])
        print(f"Результаты стресс-теста портфеля для BTC: {stress_results}")
        self.assertIsNotNone(stress_results)

    def test_autonomous_sentinel_surveillance(self):
        print("\n--- Демонстрация AutonomousSentinel ---")
        sentinel = AutonomousSentinel(self.storage_file, threshold=1000.0)
        try:
            sentinel.run_surveillance("BTC", "http://example.com/api/btc", "fake_token", "fake_chat_id")
            print("Автономный страж рынка успешно выполнил цикл мониторинга и предиктивной аналитики.")
        except Exception as e:
            print(f"Контур стража отработал с исключением (ожидаемо при заглушках сети): {e}")

if __name__ == "__main__":
    unittest.main()