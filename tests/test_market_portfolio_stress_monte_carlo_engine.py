import unittest
import unittest.mock
import uuid
import random
import math
import io
from unittest.mock import MagicMock, patch

# Импортируем тестируемый модуль
from skills import market_portfolio_stress_monte_carlo_engine


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        self.portfolio_id = uuid.uuid4().hex
        self.simulations = random.randint(100, 1000)
        self.horizon = random.randint(10, 30)
        self.initial_value = random.uniform(10000.0, 500000.0)

    def test_run_simulation_logic_integrity(self):
        """Проверка корректности расчетов VaR и CVaR при валидных данных."""
        mock_data = {
            "initial_value": self.initial_value,
            "volatility": 0.15,
            "drift": 0.02
        }

        with patch('skills.db_storage.fetch_portfolio', return_value=mock_data, create=True) as mock_db:
            with patch('skills.market_anomaly_detector.get_current_anomaly_multiplier', return_value=1.0, create=True):
                with patch('skills.market_portfolio_audit_compliance_hub.log_simulation', create=True) as mock_audit:

                    result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon)

                    self.assertEqual(result["portfolio_id"], self.portfolio_id)
                    self.assertIn("var_95", result)
                    self.assertIn("cvar_95", result)
                    self.assertTrue(result["var_95"] >= 0)
                    mock_db.assert_called_once_with(self.portfolio_id)
                    self.assertTrue(mock_audit.called)

    def test_anomaly_adjustment_fallback(self):
        """Проверка устойчивости при отсутствии метода в детекторе аномалий."""
        with patch('skills.db_storage.fetch_portfolio', return_value={"initial_value": self.initial_value}, create=True):
            with patch('skills.market_anomaly_detector.get_current_anomaly_multiplier', side_effect=AttributeError, create=True):
                # Метод должен вернуть 1.0 при ошибке
                adjustment = self.engine._get_anomaly_adjustment()
                self.assertEqual(adjustment, 1.0)

    def test_export_report_contract(self):
        """Проверка контракта экспорта с генерацией случайных параметров."""
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(100.0, 1000.0)
        
        with patch('skills.market_portfolio_data_exporter.export', create=True) as mock_export:
            expected_return = {"report_id": report_id, "status": "success"}
            mock_export.return_value = expected_return
            
            result = self.engine.export_report(report_id, loss_limit)

            self.assertEqual(result, expected_return)
            mock_export.assert_called_once_with(report_id, loss_limit)

    def test_run_monte_carlo_stress_test_execution(self):
        """Проверка функциональной целостности автономной функции стресс-теста."""
        portfolio_id = uuid.uuid4().hex
        val = random.uniform(1000.0, 10000.0)
        iterations = random.randint(50, 200)
        params = {
            "volatility": random.uniform(0.1, 0.3),
            "drift": random.uniform(-0.05, 0.05),
            "horizon_days": random.randint(1, 5)
        }

        with patch('skills.market_portfolio_audit_compliance_hub.log_simulation', create=True) as mock_audit:
            with patch('skills.market_portfolio_stress_audit_visualizer.visualize_stress_test', create=True) as mock_viz:

                result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
                    portfolio_id, val, params, iterations
                )

                self.assertEqual(result["portfolio_id"], portfolio_id)
                self.assertEqual(result["iterations"], iterations)
                self.assertIsInstance(result["simulation_id"], str)
                self.assertTrue(mock_audit.called)
                self.assertTrue(mock_viz.called)

    def test_db_storage_attribute_error_handling(self):
        """Проверка обработки отсутствия метода в хранилище через fallback."""
        with patch('skills.db_storage.fetch_portfolio', side_effect=AttributeError, create=True):
            # Имитируем отсутствие _in_memory_db для проверки инициализации
            if hasattr(market_portfolio_stress_monte_carlo_engine.db_storage, "_in_memory_db"):
                delattr(market_portfolio_stress_monte_carlo_engine.db_storage, "_in_memory_db")

            result = self.engine.run_simulation(self.portfolio_id, 10, 5)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertTrue(hasattr(market_portfolio_stress_monte_carlo_engine.db_storage, "_in_memory_db"))


if __name__ == '__main__':
    unittest.main()