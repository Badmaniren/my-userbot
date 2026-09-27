import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import run_stress_scenario_pipeline

class TestMarketPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.db")
        
        with open(self.storage_file, "w") as f:
            f.write("test_data_init")
            
        self.symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-20.0, 20.0), 2), round(random.uniform(-20.0, 20.0), 2)]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_scenario_pipeline_integration(self):
        result = run_stress_scenario_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )
        
        self.assertIsNotNone(result, "Конвейер не должен возвращать None")
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен существовать")

if __name__ == "__main__":
    unittest.main()