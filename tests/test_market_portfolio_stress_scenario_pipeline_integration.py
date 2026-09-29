import unittest
import json
import os
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)

class TestPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4().hex}.json"
        
        # Подготовка валидных начальных данных в файле хранилища, 
        # чтобы избежать падений и проверить сквозную интеграцию с реальными навыками
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.initial_data = {
            self.symbol: {
                "base_price": round(random.uniform(10.0, 1000.0), 2),
                "volume": random.randint(1000, 50000)
            }
        }
        with open(self.storage_file, "w") as f:
            json.dump(self.initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_class_execution(self):
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(self.symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        
        # Проверяем, что результаты содержат переданные параметры или связаны с ними
        self.assertEqual(result["simulation"].get("symbol"), self.symbol)

    def test_pipeline_functional_execution(self):
        percentage = round(random.uniform(-30.0, 30.0), 2)
        shifts = [round(random.uniform(-5.0, 5.0), 2) for _ in range(2)]

        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_test"].get("symbol"), self.symbol)

    def test_pipeline_with_corrupted_storage(self):
        # Намеренно портим файл хранилища некорректным JSON, чтобы проверить устойчивость пайплайна
        with open(self.storage_file, "w") as f:
            f.write("CORRUPTED_JSON_DATA_{}".format(uuid.uuid4().hex))

        percentage = round(random.uniform(-15.0, 15.0), 2)
        shifts = [round(random.uniform(-2.0, 2.0), 2)]

        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        
        # Убеждаемся, что файл хранилища был восстановлен (перезаписан корректно)
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

if __name__ == "__main__":
    unittest.main()