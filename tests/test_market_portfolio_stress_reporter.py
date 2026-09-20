import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_reporter import StressReporter

class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))

    def test_run_full_stress_report_cycle(self):
        # Генерируем случайные параметры для симуляции
        shifts = [random.uniform(-0.2, 0.2) for _ in range(3)]
        expected_report_data = f"Report_{uuid.uuid4().hex}"

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator') as MockSimulator:
            with patch('skills.market_report_generator.MarketReportGenerator') as MockGenerator:

                # Настройка моков
                instance_sim = MockSimulator.return_value
                instance_sim.run_stress_test.return_value = {"status": "success", "data": shifts}

                instance_gen = MockGenerator.return_value
                instance_gen.generate_symbol_report.return_value = expected_report_data

                reporter = StressReporter(self.storage_file)
                # Вызов тестируемого метода
                result = reporter.run_stress_report(self.symbol, shifts)

                # Проверки
                instance_sim.run_stress_test.assert_called_once_with(self.symbol, shifts)
                instance_gen.generate_symbol_report.assert_called_once_with(self.symbol)
                self.assertEqual(result, expected_report_data)

    def test_stress_reporter_initialization(self):
        # Проверка корректности передачи пути к хранилищу
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator') as MockSim:
            with patch('skills.market_report_generator.MarketReportGenerator') as MockGen:
                reporter = StressReporter(self.storage_file)

                MockSim.assert_called_with(self.storage_file)
                MockGen.assert_called_with(self.storage_file)

    def test_export_stress_stream(self):
        # Проверка обработки потока данных
        random_stream_content = uuid.uuid4().hex.encode('utf-8')

        with patch('skills.market_report_generator.MarketReportGenerator') as MockGenerator:
            instance_gen = MockGenerator.return_value
            instance_gen.get_raw_stream_dump.return_value = io.BytesIO(random_stream_content)

            reporter = StressReporter(self.storage_file)
            stream = reporter.export_stress_stream()

            self.assertEqual(stream.read(), random_stream_content)
            instance_gen.get_raw_stream_dump.assert_called_once()

    def test_scenario_failure_handling(self):
        # Проверка поведения при ошибке симулятора
        error_msg = f"Fail_{uuid.uuid4().hex}"

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator') as MockSimulator:
            instance_sim = MockSimulator.return_value
            instance_sim.run_stress_test.side_effect = Exception(error_msg)

            reporter = StressReporter(self.storage_file)
            with self.assertRaises(Exception) as context:
                reporter.run_stress_report(self.symbol, [0.1])

            self.assertTrue(error_msg in str(context.exception))

    def test_integration_logic_flow(self):
        # Проверка последовательности вызовов
        mock_sim = MagicMock()
        mock_gen = MagicMock()

        parent = MagicMock()
        parent.attach_mock(mock_sim, 'sim')
        parent.attach_mock(mock_gen, 'gen')

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator', return_value=mock_sim):
            with patch('skills.market_report_generator.MarketReportGenerator', return_value=mock_gen):
                reporter = StressReporter(self.storage_file)
                reporter.run_stress_report(self.symbol, [0.05])

                # Проверяем, что симулятор был вызван ДО генератора
                self.assertTrue(mock_sim.run_stress_test.called)
                self.assertTrue(mock_gen.generate_symbol_report.called)

                # Проверяем порядок
                sim_idx = [c[0] for c in parent.mock_calls].index('sim.run_stress_test')
                gen_idx = [c[0] for c in parent.mock_calls].index('gen.generate_symbol_report')
                self.assertLess(sim_idx, gen_idx)

if __name__ == '__main__':
    unittest.main()
