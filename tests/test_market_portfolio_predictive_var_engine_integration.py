import unittest
import uuid
import random
from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test,
)
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    MarketPortfolioStressMLVolatilityForecasterV2,
    forecast_portfolio_stress_volatility,
)
from skills.market_portfolio_predictive_var_engine import (
    MarketPortfolioPredictiveVarEngine,
    calculate_predictive_stress_var,
)


class TestMarketPortfolioPredictiveVarEngineIntegration(unittest.TestCase):
    """
    Интеграционный тест композитного модуля market_portfolio_predictive_var_engine.
    Проверяет связку реальных навыков:
    - market_portfolio_stress_monte_carlo_engine
    - market_portfolio_stress_ml_volatility_forecaster_v2
    Без использования mock-объектов между навыками.
    """

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        self.portfolio_value = round(random.uniform(100000.0, 2000000.0), 2)
        self.scenario_code = f"STRESS_{uuid.uuid4().hex[:6].upper()}"
        self.confidence_level = random.choice([0.95, 0.99])
        self.horizon_days = random.randint(5, 20)
        self.iterations = random.randint(100, 300)
        self.scenario_params = {
            "scenario_code": self.scenario_code,
            "volatility_multiplier": round(random.uniform(1.2, 2.5), 2),
            "macro_shock": round(random.uniform(0.05, 0.35), 3),
        }

    def test_calculate_predictive_stress_var_functional_flow(self):
        """Проверка функционального интерфейса calculate_predictive_stress_var с реальными данными."""
        result = calculate_predictive_stress_var(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days,
            iterations=self.iterations,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("confidence_level"), self.confidence_level)

        # Проверка наличия ключевых метрик риска
        self.assertIn("stress_var", result)
        self.assertIn("conditional_var", result)
        var_value = float(result["stress_var"])
        cvar_value = float(result["conditional_var"])

        self.assertGreater(var_value, 0.0)
        self.assertGreaterEqual(cvar_value, var_value)
        self.assertLessEqual(var_value, self.portfolio_value)

        # Проверка агрегированных результатов из зависимых навыков
        self.assertIn("ml_volatility_metrics", result)
        self.assertIsInstance(result["ml_volatility_metrics"], dict)
        self.assertIn("monte_carlo_metrics", result)
        self.assertIsInstance(result["monte_carlo_metrics"], dict)

    def test_engine_class_integration(self):
        """Проверка ООП-интерфейса MarketPortfolioPredictiveVarEngine с интеграцией зависимостей."""
        engine = MarketPortfolioPredictiveVarEngine()
        unique_port_id = f"port_{uuid.uuid4().hex}"
        rand_value = round(random.uniform(50000.0, 500000.0), 2)
        rand_iterations = random.randint(150, 400)

        result = engine.calculate_predictive_stress_var(
            portfolio_id=unique_port_id,
            portfolio_value=rand_value,
            scenario_params=self.scenario_params,
            confidence_level=0.99,
            horizon_days=10,
            iterations=rand_iterations,
        )

        self.assertEqual(result.get("portfolio_id"), unique_port_id)
        self.assertIn("stress_var", result)
        self.assertIn("conditional_var", result)
        self.assertIn("simulations_run", result)
        self.assertEqual(result["simulations_run"], rand_iterations)

        # Значение CVaR не должно быть меньше VaR в стрессовом распределении
        self.assertGreaterEqual(
            float(result["conditional_var"]),
            float(result["stress_var"])
        )

    def test_invalid_parameters_handling(self):
        """Проверка валидации некорректных параметров (отрицательный объем портфеля и уровень доверия)."""
        engine = MarketPortfolioPredictiveVarEngine()

        with self.assertRaises((ValueError, Exception)):
            engine.calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=-1000.0,
                scenario_params=self.scenario_params,
                confidence_level=0.99,
            )

        with self.assertRaises((ValueError, Exception)):
            calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                confidence_level=1.5,
            )


if __name__ == "__main__":
    unittest.main()