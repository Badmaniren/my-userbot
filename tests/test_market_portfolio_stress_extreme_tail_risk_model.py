import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os
from skills.market_portfolio_stress_extreme_tail_risk_model import (
    TailRiskModel,
    TailRiskCalculationError,
    calculate_extreme_tail_risk
)

class TestMarketPortfolioStressExtremeTailRiskModel(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.simulations = random.randint(100, 1000)
        self.file_path = f"/tmp/{uuid.uuid4().hex}.bin"

    def test_calculate_expected_shortfall_success(self):
        mock_mc_engine = MagicMock()
        mock_scenarios = [random.uniform(-0.5, 0.1) for _ in range(self.simulations)]
        mock_mc_engine.generate_scenarios.return_value = mock_scenarios

        db_mock = MagicMock()
        model = TailRiskModel(db_storage=db_mock, market_portfolio_stress_monte_carlo_engine=mock_mc_engine)

        result = model.calculate_expected_shortfall(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            simulations=self.simulations
        )

        mock_mc_engine.generate_scenarios.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            paths=self.simulations
        )
        self.assertIn("portfolio_id", result)
        self.assertIn("expected_shortfall", result)
        self.assertIn("var_at_level", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIsInstance(result["expected_shortfall"], float)
        self.assertIsInstance(result["var_at_level"], float)

    def test_calculate_expected_shortfall_empty_scenarios(self):
        mock_mc_engine = MagicMock()
        mock_mc_engine.generate_scenarios.return_value = []

        model = TailRiskModel(market_portfolio_stress_monte_carlo_engine=mock_mc_engine)

        with self.assertRaises(TailRiskCalculationError):
            model.calculate_expected_shortfall(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                simulations=self.simulations
            )

    def test_persist_tail_risk_report_with_storage(self):
        db_mock = MagicMock()
        expected_result = random.choice([True, False])
        db_mock.save_risk_report.return_value = expected_result

        model = TailRiskModel(db_storage=db_mock)
        risk_metrics = {
            "portfolio_id": self.portfolio_id,
            "expected_shortfall": random.uniform(-0.2, -0.05),
            "var_at_level": random.uniform(-0.15, -0.01)
        }

        res = model.persist_tail_risk_report(risk_metrics)
        db_mock.save_risk_report.assert_called_once_with(risk_metrics)
        self.assertEqual(res, expected_result)

    def test_persist_tail_risk_report_no_storage(self):
        model = TailRiskModel(db_storage=None)
        risk_metrics = {
            "portfolio_id": self.portfolio_id,
            "expected_shortfall": random.uniform(-0.2, -0.05),
            "var_at_level": random.uniform(-0.15, -0.01)
        }

        res = model.persist_tail_risk_report(risk_metrics)
        self.assertFalse(res)

    def test_load_binary_stress_stream(self):
        model = TailRiskModel()
        random_bytes = os.urandom(64)

        with patch("builtins.open", return_value=io.BytesIO(random_bytes)) as mock_file:
            data = model.load_binary_stress_stream(self.file_path)
            mock_file.assert_called_once_with(self.file_path, "rb")
            self.assertEqual(data, random_bytes)

    def test_calculate_extreme_tail_risk_success(self):
        scenario_data = [random.uniform(-0.4, 0.2) for _ in range(500)]
        result = calculate_extreme_tail_risk(
            portfolio_id=self.portfolio_id,
            scenario_data=scenario_data,
            confidence=self.confidence_level
        )

        self.assertIn("portfolio_id", result)
        self.assertIn("expected_shortfall", result)
        self.assertIn("var_metric", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIsInstance(result["expected_shortfall"], float)
        self.assertIsInstance(result["var_metric"], float)

    def test_calculate_extreme_tail_risk_empty_data(self):
        with self.assertRaises(TailRiskCalculationError):
            calculate_extreme_tail_risk(
                portfolio_id=self.portfolio_id,
                scenario_data=[],
                confidence=self.confidence_level
            )