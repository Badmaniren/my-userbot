import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_stress_diagnostic_telemetry_v2 import (
    market_portfolio_stress_diagnostic_telemetry_v2,
    db_storage,
    market_portfolio_collector_agent,
    market_portfolio_stress_scenario_pipeline
)

class TestMarketPortfolioStressDiagnosticTelemetryV2Integration(unittest.TestCase):
    def setUp(self):
        self.test_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.test_session_id = str(uuid.uuid4())
        self.test_metric_value = round(random.uniform(10500.5, 99999.9), 2)
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_telemetry_diagnostic_flow(self):
        # 1. Подготовка окружения через реальный сборщик и пайплайн сценариев стресс-теста
        collector_input = {
            "portfolio_id": self.test_portfolio_id,
            "session_id": self.test_session_id,
            "initial_capital": self.test_metric_value,
            "volatility_index": random.choice([0.15, 0.22, 0.35, 0.50])
        }

        # Вызов смежных реальных модулей для формирования цепочки данных без моков
        collected_data = market_portfolio_collector_agent(collector_input)
        self.assertIsNotNone(collected_data)

        scenario_result = market_portfolio_stress_scenario_pipeline(collected_data)
        self.assertIsNotNone(scenario_result)

        # 2. Основной вызов тестируемого модуля телеметрии
        telemetry_payload = {
            "session_id": self.test_session_id,
            "portfolio_id": self.test_portfolio_id,
            "scenario_metrics": scenario_result,
            "target_storage_path": self.temp_dir.name
        }

        telemetry_response = market_portfolio_stress_diagnostic_telemetry_v2(telemetry_payload)

        # 3. Проверка возвращаемых реальных данных и уникальных ID
        self.assertIsInstance(telemetry_response, dict)
        self.assertIn("diagnostic_id", telemetry_response)
        self.assertEqual(telemetry_response["session_id"], self.test_session_id)
        self.assertEqual(telemetry_response["status"], "success")

        # 4. Проверка реального изменения состояния (запись в хранилище / появление файлов телеметрии)
        storage_check = db_storage({
            "action": "get_telemetry",
            "session_id": self.test_session_id
        })
        self.assertIsNotNone(storage_check)

        expected_file_name = f"telemetry_{self.test_session_id}.json"
        generated_files = os.listdir(self.temp_dir.name)
        self.assertTrue(
            any(expected_file_name in f or f.endswith(".log") or f.endswith(".json") for f in generated_files),
            "Телеметрия не создала физических артефактов в целевой директории"
        )

if __name__ == "__main__":
    unittest.main()