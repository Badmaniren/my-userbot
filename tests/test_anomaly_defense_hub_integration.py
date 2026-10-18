import unittest
import uuid
import random
import os
import tempfile
from skills.anomaly_defense_hub import AnomalyDefenseHub
from skills.anomaly_forecaster import AnomalyForecaster
from skills.anomaly_reactor import AutonomousReactorEngine

class TestAnomalyDefenseHubIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"test_log_{uuid.uuid4()}.json")
        self.model_name = f"model_{uuid.uuid4()}"
        self.threshold = random.uniform(0.5, 0.9)

        self.forecaster = AnomalyForecaster(
            log_path=self.log_path,
            model_name=self.model_name,
            threshold=self.threshold
        )
        self.reactor = AutonomousReactorEngine()

        self.defense_hub = AnomalyDefenseHub(
            forecaster=self.forecaster,
            reactor=self.reactor
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_defense_hub_real_composition_workflow(self):
        random_metric = random.randint(100, 1000)
        random_cpu = round(random.uniform(10.0, 99.9), 2)
        random_id = str(uuid.uuid4())

        telemetry_data = {
            "id": random_id,
            "metric": random_metric,
            "cpu_usage": random_cpu,
            "status": "unstable"
        }

        # Обучаем предсказатель на базовых данных, чтобы модель не была пустой
        training_stream = [
            {"metric": 50, "cpu_usage": 15.0},
            {"metric": 55, "cpu_usage": 18.0},
            {"metric": 52, "cpu_usage": 16.0}
        ]
        self.forecaster.train(training_stream)

        # Запускаем полный интеграционный цикл защиты через DefenseHub
        defense_result = self.defense_hub.process_telemetry(telemetry_data)

        self.assertIsNotNone(defense_result)
        self.assertIn("forecast", defense_result)
        self.assertIn("reaction", defense_result)

        forecast = defense_result["forecast"]
        self.assertTrue(hasattr(forecast, "is_anomaly"))
        self.assertTrue(hasattr(forecast, "confidence_score"))

        reaction = defense_result["reaction"]
        self.assertIsInstance(reaction, dict)
        self.assertIn("status", reaction)

if __name__ == "__main__":
    unittest.main()