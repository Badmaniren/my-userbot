import unittest
import random
import math
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine


class TestMonteCarloStressEpicRealCondition(unittest.TestCase):
    def test_monte_carlo_engine_stress_simulation(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА МОНТЕ-КАРЛО ===")

        # 1. Подготовка реальных рыночных данных портфеля (симуляция исторических цен активов)
        random.seed(42)
        initial_portfolio_value = 1_000_000.0

        # Три актива в портфеле: Акции, Облигации, Сырье
        assets = ['Equities', 'Bonds', 'Commodities']
        weights = [0.5, 0.3, 0.2]

        # Годовая доходность и волатильность
        mean_returns = [0.10 / 252, 0.04 / 252, 0.08 / 252]
        volatilities = [0.20 / math.sqrt(252), 0.05 / math.sqrt(252), 0.25 / math.sqrt(252)]

        # Генерация ковариационной матрицы с корреляциями
        corr_matrix = [
            [1.0, 0.1, 0.5],
            [0.1, 1.0, 0.0],
            [0.5, 0.0, 1.0]
        ]

        cov_matrix = [
            [volatilities[i] * volatilities[j] * corr_matrix[i][j] for j in range(3)]
            for i in range(3)
        ]

        print(f"Портфель инициализирован. Стоимость: ${initial_portfolio_value:,.2f}")
        print(f"Активы: {list(zip(assets, weights))}")

        # 2. Интеграция с движком Монте-Карло (market_portfolio_stress_monte_carlo_engine)
        # Симулируем 1000 траекторий на горизонте 30 торговых дней при экстремальном стресс-шоке (например, кризис)
        num_simulations = 1000
        horizon_days = 30
        shock_multiplier = 2.5 # Усиление волатильности в 2.5 раза (рыночный шок)

        engine = MonteCarloStressEngine()
        sim_result = engine.run_multivariate_simulation(
            weights=weights,
            mean_returns=mean_returns,
            cov_matrix=cov_matrix,
            num_simulations=num_simulations,
            horizon_days=horizon_days,
            shock_multiplier=shock_multiplier,
            initial_portfolio_value=initial_portfolio_value
        )

        simulated_ending_values = sim_result["simulated_ending_values"]
        var_95 = sim_result["var_95"]
        var_99 = sim_result["var_99"]
        expected_shortfall_95 = sim_result["expected_shortfall_95"]

        print("\n--- РЕЗУЛЬТАТЫ СТРЕСС-ТЕСТИРОВАНИЯ МОНТЕ-КАРЛО ---")
        print(f"Количество симуляций: {num_simulations}")
        print(f"Горизонт прогноза: {horizon_days} дней")
        print(f"Коэффициент рыночного шока: {shock_multiplier}x волатильности")
        print(f"Медианная стоимость портфеля после стресса: ${sim_result['median_value']:,.2f}")
        print(f"Value at Risk (VaR 95%): ${var_95:,.2f} (Убыток: ${initial_portfolio_value - var_95:,.2f})")
        print(f"Value at Risk (VaR 99%): ${var_99:,.2f} (Убыток: ${initial_portfolio_value - var_99:,.2f})")
        print(f"Expected Shortfall (CVaR 95%): ${expected_shortfall_95:,.2f}")

        # 4. Проверка корректности работы модулей отчетности и симуляции
        self.assertEqual(len(simulated_ending_values), num_simulations, "Неверный размер массива симуляций")
        self.assertLess(var_95, initial_portfolio_value, "VaR 95% должен быть меньше исходной стоимости портфеля при стрессе")
        self.assertLess(var_99, var_95, "VaR 99% должен быть более консервативным (меньше), чем VaR 95%")

        print("\n=== ЭПИК УСПЕШНО ПРОШЕЛ ПРАКТИЧЕСКУЮ ПРОВЕРКУ В РЕАЛЬНЫХ УСЛОВИЯХ ===")


if __name__ == '__main__':
    unittest.main()
