import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import uuid
import random
import io
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
        self.percentage = random.uniform(0.01, 0.5)
        self.shifts = [random.uniform(-0.1, 0.1) for _ in range(3)]

    def test_execute_success_flow(self):
        mock_sim_result = {"simulated_value": random.uniform(100, 1000)}
        mock_stress_result = [random.uniform(-0.05, 0.05) for _ in range(3)]
        mock_report_result = {"status": "critical", "impact_score": random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim:
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep:
                instance = MockSim.return_value
                instance.simulate_scenario.return_value = mock_sim_result
                instance.run_stress_test.return_value = mock_stress_result
                
                reporter_instance = MockRep.return_value
                reporter_instance.run_stress_report.return_value = mock_report_result

                with patch("builtins.open", mock_open(read_data=json.dumps({}))) as mocked_file:
                    pipeline = PortfolioStressScenarioPipeline(self.storage_file)
                    result = pipeline.execute(self.symbol, self.percentage, self.shifts)

                    self.assertEqual(result["simulation"]["symbol"], self.symbol)
                    self.assertEqual(result["stress_test"]["results"], mock_stress_result)
                    self.assertEqual(result["stress_report"]["impact_score"], mock_report_result["impact_score"])
                    mocked_file.assert_called()

    def test_execute_handles_simulator_exceptions(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim:
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep:
                instance = MockSim.return_value
                instance.simulate_scenario.side_effect = RuntimeError("Sim fail")
                instance.run_stress_test.side_effect = KeyError("Test fail")
                
                reporter_instance = MockRep.return_value
                reporter_instance.run_stress_report.side_effect = AttributeError("Report fail")

                with patch("builtins.open", mock_open(read_data=json.dumps({}))):
                    pipeline = PortfolioStressScenarioPipeline(self.storage_file)
                    result = pipeline.execute(self.symbol, self.percentage, self.shifts)

                    self.assertEqual(result["simulation"]["simulated_value"], 0.0)
                    self.assertEqual(result["stress_test"]["results"], [])
                    self.assertEqual(result["stress_report"]["status"], "default")

    def test_storage_initialization_on_invalid_file(self):
        # Имитируем битый JSON
        corrupted_data = "INVALID_JSON_CONTENT_" + uuid.uuid4().hex
        
        with patch("builtins.open", mock_open(read_data=corrupted_data)) as mocked_file:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            
            # Проверяем, что была попытка записи пустого словаря при ошибке чтения
            mocked_file.assert_any_call(self.storage_file, "w", encoding="utf-8")
            handle = mocked_file()
            handle.write.assert_called_with("{}")

    def test_execute_data_normalization(self):
        # Проверка, что pipeline дополняет отсутствующие ключи в ответах
        incomplete_sim = {"custom_key": random.random()}
        
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim:
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep:
                instance = MockSim.return_value
                instance.simulate_scenario.return_value = incomplete_sim
                instance.run_stress_test.return_value = []
                
                reporter_instance = MockRep.return_value
                reporter_instance.run_stress_report.return_value = {}

                with patch("builtins.open", mock_open(read_data=json.dumps({}))):
                    pipeline = PortfolioStressScenarioPipeline(self.storage_file)
                    result = pipeline.execute(self.symbol, self.percentage, self.shifts)

                    self.assertEqual(result["simulation"]["symbol"], self.symbol)
                    self.assertEqual(result["simulation"]["percentage"], self.percentage)
                    self.assertEqual(result["stress_report"]["symbol"], self.symbol)

if __name__ == "__main__":
    unittest.main()