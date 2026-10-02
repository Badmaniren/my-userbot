import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import sys

class MockNumpy:
    @staticmethod
    def mean(values):
        if not values:
            return 0.0
        return sum(values) / len(values)

sys.modules['numpy'] = MockNumpy

class MockMatplotlibPyplot:
    @staticmethod
    def figure(*args, **kwargs):
        pass
    @staticmethod
    def hist(*args, **kwargs):
        pass
    @staticmethod
    def title(*args, **kwargs):
        pass
    @staticmethod
    def xlabel(*args, **kwargs):
        pass
    @staticmethod
    def ylabel(*args, **kwargs):
        pass
    @staticmethod
    def savefig(*args, **kwargs):
        pass
    @staticmethod
    def close(*args, **kwargs):
        pass

sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MockMatplotlibPyplot

from skills.market_portfolio_tail_risk_visualizer import (
    TailRiskVisualizer,
    TailRiskCalculationError,
    market_portfolio_tail_risk_visualizer
)

class TestMarketPortfolioTailRiskVisualizer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.simulations = random.randint(50, 500)
        self.confidence = random.uniform(0.90, 0.99)
        self.output_filename = f"{uuid.uuid4().hex}.png"
        self.metric_name = f"metric_{uuid.uuid4().hex}"
        self.metric_value = random.uniform(-50000.0, -1000.0)

    def test_generate_tail_risk_plot_success(self):
        mock_engine = MagicMock()
        rand_losses = [random.uniform(-10000, -100) for _ in range(self.simulations)]
        mock_engine.run_simulations.return_value = rand_losses

        visualizer = TailRiskVisualizer(market_portfolio_stress_monte_carlo_engine=mock_engine)

        result = visualizer.generate_tail_risk_plot(
            self.portfolio_id,
            self.simulations,
            self.confidence,
            self.output_filename
        )

        mock_engine.run_simulations.assert_called_once_with(self.portfolio_id, self.simulations)
        self.assertEqual(result, self.output_filename)

    def test_generate_tail_risk_plot_empty_data(self):
        mock_engine = MagicMock()
        mock_engine.run_simulations.return_value = []

        visualizer = TailRiskVisualizer(market_portfolio_stress_monte_carlo_engine=mock_engine)

        with self.assertRaises(TailRiskCalculationError):
            visualizer.generate_tail_risk_plot(
                self.portfolio_id,
                self.simulations,
                self.confidence,
                self.output_filename
            )

    def test_calculate_var_cvar_metrics(self):
        mock_engine = MagicMock()
        rand_losses = [float(i * -100) for i in range(1, 201)]
        random.shuffle(rand_losses)
        mock_engine.run_simulations.return_value = rand_losses

        visualizer = TailRiskVisualizer(market_portfolio_stress_monte_carlo_engine=mock_engine)
        var, cvar = visualizer.calculate_var_cvar_metrics(self.portfolio_id, self.confidence)

        mock_engine.run_simulations.assert_called_once_with(self.portfolio_id, 200)
        self.assertIsInstance(var, float)
        self.assertIsInstance(cvar, float)

    def test_export_report_stream(self):
        mock_engine = MagicMock()
        rand_losses = [random.uniform(-5000, -50) for _ in range(50)]
        mock_engine.run_simulations.return_value = rand_losses

        visualizer = TailRiskVisualizer(market_portfolio_stress_monte_carlo_engine=mock_engine)
        stream = io.BytesIO()

        visualizer.export_report_stream(self.portfolio_id, stream)

        mock_engine.run_simulations.assert_called_once_with(self.portfolio_id, 50)
        self.assertEqual(stream.tell(), 0)

    def test_persist_tail_risk_snapshot_with_storage(self):
        mock_engine = MagicMock()
        mock_storage = MagicMock()
        rand_losses = [random.uniform(-8000, -200) for _ in range(150)]
        mock_engine.run_simulations.return_value = rand_losses

        visualizer = TailRiskVisualizer(
            db_storage=mock_storage,
            market_portfolio_stress_monte_carlo_engine=mock_engine
        )

        visualizer.persist_tail_risk_snapshot(self.portfolio_id, self.metric_name, self.metric_value)

        mock_engine.run_simulations.assert_called_once_with(self.portfolio_id, 150)
        mock_storage.save_risk_metric.assert_called_once_with(
            self.portfolio_id,
            self.metric_name,
            self.metric_value
        )

    def test_persist_tail_risk_snapshot_without_storage(self):
        mock_engine = MagicMock()
        rand_losses = [random.uniform(-8000, -200) for _ in range(150)]
        mock_engine.run_simulations.return_value = rand_losses

        visualizer = TailRiskVisualizer(
            db_storage=None,
            market_portfolio_stress_monte_carlo_engine=mock_engine
        )

        try:
            visualizer.persist_tail_risk_snapshot(self.portfolio_id, self.metric_name, self.metric_value)
        except Exception as e:
            self.fail(f"persist_tail_risk_snapshot raised exception without db_storage: {e}")

    @patch('skills.market_portfolio_tail_risk_visualizer.db_storage')
    def test_market_portfolio_tail_risk_visualizer_handler(self, mock_db_storage):
        simulation_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": self.portfolio_id,
            "simulation_id": simulation_id
        }

        result = market_portfolio_tail_risk_visualizer(payload)

        self.assertIn("chart_artifact_id", result)
        self.assertIn("tail_var", result)
        self.assertIsInstance(result["chart_artifact_id"], str)
        self.assertEqual(result["tail_var"], -15000.0)
        mock_db_storage.assert_called_once()
        called_args = mock_db_storage.call_args[0][0]
        self.assertEqual(called_args["action"], "save")
        self.assertEqual(called_args["value"]["portfolio_id"], self.portfolio_id)
        self.assertEqual(called_args["value"]["simulation_id"], simulation_id)

if __name__ == '__main__':
    unittest.main()