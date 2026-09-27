import io
import os
import random
import string
import sys
import unittest
import uuid
from unittest.mock import MagicMock, patch

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    import skills.market_portfolio_simulation_evaluator as target_module
except ImportError:
    import market_portfolio_simulation_evaluator as target_module


def _random_str(prefix="str_"):
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def _random_symbol():
    letters = "".join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))
    return f"{letters}_{uuid.uuid4().hex[:4].upper()}"


def _random_file_path():
    return f"/tmp/{uuid.uuid4().hex}/{_random_str('store')}.json"


class TestMarketPortfolioSimulationEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator_class = getattr(
            target_module,
            "PortfolioSimulationEvaluator",
            getattr(target_module, "MarketPortfolioSimulationEvaluator", None),
        )
        self.assertIsNotNone(
            self.evaluator_class,
            "Модуль должен определять класс PortfolioSimulationEvaluator или MarketPortfolioSimulationEvaluator",
        )

    def test_module_imports_required_dependencies(self):
        self.assertTrue(
            hasattr(target_module, "market_portfolio_scenario_simulator")
            or hasattr(target_module, "PortfolioScenarioSimulator")
            or "market_portfolio_scenario_simulator" in target_module.__dict__,
            "Модуль обязан импортировать 'market_portfolio_scenario_simulator'",
        )
        self.assertTrue(
            hasattr(target_module, "market_portfolio_performance_analytics")
            or hasattr(target_module, "PortfolioPerformanceAnalytics")
            or "market_portfolio_performance_analytics" in target_module.__dict__,
            "Модуль обязан импортировать 'market_portfolio_performance_analytics'",
        )

    def test_init_instantiates_underlying_skills(self):
        random_storage = _random_file_path()

        with patch(
            "market_portfolio_scenario_simulator.PortfolioScenarioSimulator"
        ) as mock_sim_cls, patch(
            "market_portfolio_performance_analytics.PortfolioPerformanceAnalytics"
        ) as mock_perf_cls:
            evaluator = self.evaluator_class(storage_file=random_storage)

            mock_sim_cls.assert_called_once_with(random_storage)
            mock_perf_cls.assert_called_once_with(random_storage)
            self.assertIsNotNone(evaluator)

    def test_evaluate_scenario_combines_simulation_and_performance(self):
        random_storage = _random_file_path()
        random_symbol = _random_symbol()
        random_percentage = round(random.uniform(-45.0, 45.0), 4)

        sim_key = f"sim_metric_{uuid.uuid4().hex[:6]}"
        sim_val = round(random.uniform(100.0, 5000.0), 2)
        sim_response = {sim_key: sim_val, "symbol": random_symbol}

        perf_key = f"perf_metric_{uuid.uuid4().hex[:6]}"
        perf_val = round(random.uniform(0.01, 0.99), 4)
        perf_response = {perf_key: perf_val, "status": "calculated"}

        with patch(
            "market_portfolio_scenario_simulator.PortfolioScenarioSimulator"
        ) as mock_sim_cls, patch(
            "market_portfolio_performance_analytics.PortfolioPerformanceAnalytics"
        ) as mock_perf_cls:

            sim_instance = mock_sim_cls.return_value
            sim_instance.simulate_scenario.return_value = sim_response

            perf_instance = mock_perf_cls.return_value
            perf_instance.calculate_metrics.return_value = perf_response
            perf_instance.evaluate_performance.return_value = perf_response

            evaluator = self.evaluator_class(storage_file=random_storage)

            eval_method = getattr(
                evaluator,
                "evaluate_scenario",
                getattr(evaluator, "simulate_and_evaluate", None),
            )
            self.assertIsNotNone(
                eval_method,
                "Класс должен предоставлять метод 'evaluate_scenario' или 'simulate_and_evaluate'",
            )

            result = eval_method(random_symbol, random_percentage)

            sim_instance.simulate_scenario.assert_called_once_with(
                random_symbol, random_percentage
            )
            self.assertTrue(
                perf_instance.calculate_metrics.called
                or perf_instance.evaluate_performance.called,
                "Аналитика производительности должна быть вызвана при оценке сценария",
            )

            self.assertIsInstance(result, dict)
            result_str = str(result)
            self.assertIn(sim_key, result_str)
            self.assertIn(str(sim_val), result_str)
            self.assertIn(perf_key, result_str)
            self.assertIn(str(perf_val), result_str)

    def test_evaluate_stress_test_aggregates_shifts_and_metrics(self):
        random_storage = _random_file_path()
        random_symbol = _random_symbol()
        random_shifts = [
            round(random.uniform(-50.0, 50.0), 2) for _ in range(random.randint(2, 6))
        ]

        stress_token = f"stress_token_{uuid.uuid4().hex[:8]}"
        sim_stress_result = {
            "token": stress_token,
            "shifts_tested": random_shifts,
            "max_drawdown": round(random.uniform(0.1, 0.8), 3),
        }

        perf_token = f"perf_token_{uuid.uuid4().hex[:8]}"
        perf_result = {
            "token": perf_token,
            "sharpe_ratio": round(random.uniform(0.5, 3.5), 2),
        }

        with patch(
            "market_portfolio_scenario_simulator.PortfolioScenarioSimulator"
        ) as mock_sim_cls, patch(
            "market_portfolio_performance_analytics.PortfolioPerformanceAnalytics"
        ) as mock_perf_cls:

            sim_instance = mock_sim_cls.return_value
            sim_instance.run_stress_test.return_value = sim_stress_result

            perf_instance = mock_perf_cls.return_value
            perf_instance.evaluate_performance.return_value = perf_result
            perf_instance.calculate_metrics.return_value = perf_result

            evaluator = self.evaluator_class(storage_file=random_storage)

            stress_method = getattr(
                evaluator,
                "evaluate_stress_test",
                getattr(evaluator, "run_stress_evaluation", None),
            )
            self.assertIsNotNone(
                stress_method,
                "Класс должен предоставлять метод 'evaluate_stress_test' или 'run_stress_evaluation'",
            )

            result = stress_method(random_symbol, random_shifts)

            sim_instance.run_stress_test.assert_called_once_with(
                random_symbol, random_shifts
            )

            self.assertIsInstance(result, dict)
            result_str = str(result)
            self.assertIn(stress_token, result_str)
            self.assertIn(perf_token, result_str)

    def test_standalone_convenience_function_execution(self):
        func = getattr(
            target_module,
            "evaluate_portfolio_simulation",
            getattr(target_module, "evaluate_market_scenario", None),
        )
        if func is None:
            self.skipTest(
                "Модуль не экспортирует автономную функцию 'evaluate_portfolio_simulation'/'evaluate_market_scenario'"
            )

        random_storage = _random_file_path()
        random_symbol = _random_symbol()
        random_percentage = round(random.uniform(-30.0, 30.0), 3)

        expected_rand_marker = f"result_marker_{uuid.uuid4().hex}"

        with patch(
            "market_portfolio_scenario_simulator.PortfolioScenarioSimulator"
        ) as mock_sim_cls, patch(
            "market_portfolio_performance_analytics.PortfolioPerformanceAnalytics"
        ) as mock_perf_cls:

            sim_instance = mock_sim_cls.return_value
            sim_instance.simulate_scenario.return_value = {
                "sim_data": expected_rand_marker
            }

            perf_instance = mock_perf_cls.return_value
            perf_instance.calculate_metrics.return_value = {"status": "ok"}
            perf_instance.evaluate_performance.return_value = {"status": "ok"}

            res = func(random_storage, random_symbol, random_percentage)

            self.assertIsInstance(res, dict)
            self.assertIn(expected_rand_marker, str(res))

    def test_handles_simulator_error_propagation_or_graceful_capture(self):
        random_storage = _random_file_path()
        random_symbol = _random_symbol()
        random_percentage = round(random.uniform(5.0, 15.0), 2)
        error_message = f"SimulationCrash_{uuid.uuid4().hex}"

        with patch(
            "market_portfolio_scenario_simulator.PortfolioScenarioSimulator"
        ) as mock_sim_cls, patch(
            "market_portfolio_performance_analytics.PortfolioPerformanceAnalytics"
        ):

            sim_instance = mock_sim_cls.return_value
            sim_instance.simulate_scenario.side_effect = RuntimeError(error_message)

            evaluator = self.evaluator_class(storage_file=random_storage)
            eval_method = getattr(
                evaluator,
                "evaluate_scenario",
                getattr(evaluator, "simulate_and_evaluate", None),
            )

            try:
                result = eval_method(random_symbol, random_percentage)
                self.assertIsInstance(result, dict)
                self.assertTrue(
                    "error" in result
                    or "failed" in str(result).lower()
                    or error_message in str(result),
                    "При перехвате ошибки результат должен отражать сбой симуляции",
                )
            except RuntimeError as ex:
                self.assertIn(error_message, str(ex))

    def test_stream_data_loading_if_supported(self):
        random_storage = _random_file_path()
        evaluator = None

        with patch(
            "market_portfolio_scenario_simulator.PortfolioScenarioSimulator"
        ), patch(
            "market_portfolio_performance_analytics.PortfolioPerformanceAnalytics"
        ):
            evaluator = self.evaluator_class(storage_file=random_storage)

        load_method = getattr(evaluator, "load_data", None)
        if callable(load_method):
            random_bytes = uuid.uuid4().hex.encode("utf-8")
            stream_mock = io.BytesIO(random_bytes)
            with patch("builtins.open", return_value=stream_mock):
                target_file = _random_file_path()
                try:
                    load_method(target_file)
                except Exception as e:
                    self.fail(f"Метод load_data упал при обработке потока: {e}")


if __name__ == "__main__":
    unittest.main()
