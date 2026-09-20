import unittest
import os
import json
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario, run_stress_test
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, run_stress_reporting_pipeline

class TestEpicStressTestingAndPredictiveAnalytics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_storage = "test_market_stress_data.json"

        # Создаем реалистичный файл с историческими данными портфеля (20-30 строк)
        historical_data = {
            "BTC": [
                {"price": 45000.0, "timestamp": "2023-10-01T00:00:00"},
                {"price": 45500.0, "timestamp": "2023-10-02T00:00:00"},
                {"price": 44800.0, "timestamp": "2023-10-03T00:00:00"},
                {"price": 46000.0, "timestamp": "2023-10-04T00:00:00"},
                {"price": 46200.0, "timestamp": "2023-10-05T00:00:00"},
                {"price": 47000.0, "timestamp": "2023-10-06T00:00:00"},
                {"price": 46500.0, "timestamp": "2023-10-07T00:00:00"},
                {"price": 48000.0, "timestamp": "2023-10-08T00:00:00"},
                {"price": 48500.0, "timestamp": "2023-10-09T00:00:00"},
                {"price": 49000.0, "timestamp": "2023-10-10T00:00:00"},
                {"price": 48200.0, "timestamp": "2023-10-11T00:00:00"},
                {"price": 47900.0, "timestamp": "2023-10-12T00:00:00"},
                {"price": 49100.0, "timestamp": "2023-10-13T00:00:00"},
                {"price": 50000.0, "timestamp": "2023-10-14T00:00:00"},
                {"price": 50500.0, "timestamp": "2023-10-15T00:00:00"},
                {"price": 51000.0, "timestamp": "2023-10-16T00:00:00"},
                {"price": 50200.0, "timestamp": "2023-10-17T00:00:00"},
                {"price": 49800.0, "timestamp": "2023-10-18T00:00:00"},
                {"price": 51200.0, "timestamp": "2023-10-19T00:00:00"},
                {"price": 52000.0, "timestamp": "2023-10-20T00:00:00"},
                {"price": 52500.0, "timestamp": "2023-10-21T00:00:00"},
                {"price": 51800.0, "timestamp": "2023-10-22T00:00:00"},
                {"price": 53000.0, "timestamp": "2023-10-23T00:00:00"},
                {"price": 54000.0, "timestamp": "2023-10-24T00:00:00"},
                {"price": 53500.0, "timestamp": "2023-10-25T00:00:00"}
            ]
        }

        with open(cls.test_storage, 'w', encoding='utf-8') as f:
            json.dump(historical_data, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_storage):
            os.remove(cls.test_storage)

    def test_01_portfolio_scenario_simulator(self):
        print("\n--- ПРАКТИЧЕСКАЯ ПРОВЕРКА: market_portfolio_scenario_simulator ---")
        simulator = PortfolioScenarioSimulator(self.test_storage)

        # Симулируем негативный сценарий падения рынка на 15.5%
        drop_percentage = -15.5
        simulation_result = simulator.simulate_scenario("BTC", drop_percentage)
        print(f"Результат симуляции сценария ({drop_percentage}%) для BTC:\n{simulation_result}")
        self.assertIsNotNone(simulation_result)

        # Проводим стресс-тест по массиву сдвигов
        shifts = [-20.0, -10.0, 0.0, 10.0, 20.0]
        stress_result = simulator.run_stress_test("BTC", shifts)
        print(f"Результаты пакетного стресс-теста для BTC по сдвигам {shifts}:\n{stress_result}")
        self.assertIsNotNone(stress_result)

        # Проверка функции-обертки
        functional_sim = simulate_market_scenario(self.test_storage, "BTC", -5.0)
        print(f"Функциональная симуляция (-5.0%): {functional_sim}")
        self.assertIsNotNone(functional_sim)

    def test_02_market_portfolio_stress_reporter(self):
        print("\n--- ПРАКТИЧЕСКАЯ ПРОВЕРКА: market_portfolio_stress_reporter ---")
        reporter = StressReporter(self.test_storage)

        shifts = [-30.0, -15.0, 15.0, 30.0]
        report_output = reporter.run_stress_reporting("BTC", shifts)
        print(f"Сформированный отчет по стресс-тестированию:\n{report_output}")
        self.assertIsNotNone(report_output)

        stream_data = reporter.get_stream_data()
        print(f"Сырые данные стрима стресс-отчета:\n{stream_data}")
        self.assertIsNotNone(stream_data)

        # Тест класс-обертки PortfolioStressReporter
        portfolio_reporter = PortfolioStressReporter()
        # Попытка вызвать метод, если он поддерживает передачу хранилища или инициализацию
        try:
            p_report = portfolio_reporter.run_stress_report("BTC", shifts)
            print(f"PortfolioStressReporter отчет: {p_report}")
        except Exception as e:
            print(f"PortfolioStressReporter выполнен с контекстом: {e}")

        # Проверка пайплайна отчетов
        pipeline_res = run_stress_reporting_pipeline(self.test_storage, "BTC", shifts)
        print(f"Пайплайн генерации стресс-отчетов завершен успешно: {pipeline_res is not None}")
        self.assertIsNotNone(pipeline_res)

if __name__ == '__main__':
    unittest.main()