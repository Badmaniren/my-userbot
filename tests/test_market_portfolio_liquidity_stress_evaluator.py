import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import sys
import io

try:
    import skills.market_portfolio_liquidity_stress_evaluator as evaluator_module
except ImportError:
    import market_portfolio_liquidity_stress_evaluator as evaluator_module


class TestMarketPortfolioLiquidityStressEvaluator(unittest.TestCase):
    def setUp(self):
        self.random_portfolio_id = "port-" + uuid.uuid4().hex
        self.random_symbol = "".join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))
        self.random_percentage = round(random.uniform(5.0, 75.0), 3)
        self.random_storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.random_export_target = f"export_{uuid.uuid4().hex}.json"
        self.random_confidence = random.choice([0.90, 0.95, 0.975, 0.99])
        self.random_shifts = {
            f"factor_{uuid.uuid4().hex[:6]}": round(random.uniform(-0.5, 0.5), 4)
            for _ in range(random.randint(2, 5))
        }

    def _get_target_class(self):
        if hasattr(evaluator_module, "MarketPortfolioLiquidityStressEvaluator"):
            return getattr(evaluator_module, "MarketPortfolioLiquidityStressEvaluator")
        elif hasattr(evaluator_module, "PortfolioLiquidityStressEvaluator"):
            return getattr(evaluator_module, "PortfolioLiquidityStressEvaluator")
        else:
            self.fail("Evaluator class not found in module")

    def test_module_imports_required_dependencies(self):
        self.assertTrue(
            hasattr(evaluator_module, "market_portfolio_var_liquidity_core")
            or "market_portfolio_var_liquidity_core" in sys.modules,
            "Module must import and use 'market_portfolio_var_liquidity_core'"
        )
        self.assertTrue(
            hasattr(evaluator_module, "market_portfolio_stress_scenario_pipeline")
            or "market_portfolio_stress_scenario_pipeline" in sys.modules,
            "Module must import and use 'market_portfolio_stress_scenario_pipeline'"
        )

    def test_evaluate_stress_success(self):
        EvaluatorClass = self._get_target_class()
        mock_var_loss = round(random.uniform(1000.0, 25000.0), 2)
        mock_liquidity_score = round(random.uniform(0.1, 0.9), 3)
        mock_stress_loss = round(random.uniform(50000.0, 150000.0), 2)

        var_payload = {
            "portfolio_id": self.random_portfolio_id,
            "var_value": mock_var_loss,
            "liquidity_score": mock_liquidity_score,
            "status": "success"
        }
        stress_payload = {
            "symbol": self.random_symbol,
            "projected_loss": mock_stress_loss,
            "shifts": self.random_shifts,
            "status": "executed"
        }

        with patch("skills.market_portfolio_liquidity_stress_evaluator.market_portfolio_var_liquidity_core") as mock_var_core, \
             patch("skills.market_portfolio_liquidity_stress_evaluator.PortfolioStressScenarioPipeline") as mock_pipeline_cls:
            
            mock_var_instance = MagicMock()
            if hasattr(mock_var_core, "market_portfolio_var_liquidity_core"):
                mock_var_core.market_portfolio_var_liquidity_core.return_value = mock_var_instance
            mock_var_core.calculate_var_and_liquidity.return_value = var_payload
            mock_var_instance.calculate_var_and_liquidity.return_value = var_payload

            mock_pipeline_instance = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_instance
            mock_pipeline_instance.execute.return_value = stress_payload

            evaluator = EvaluatorClass(storage_file=self.random_storage_file)

            if hasattr(evaluator, "evaluate_stress"):
                result = evaluator.evaluate_stress(
                    portfolio_id=self.random_portfolio_id,
                    symbol=self.random_symbol,
                    percentage=self.random_percentage,
                    shifts=self.random_shifts,
                    confidence_level=self.random_confidence,
                    export_target=self.random_export_target
                )
            elif hasattr(evaluator, "execute"):
                result = evaluator.execute(
                    portfolio_id=self.random_portfolio_id,
                    symbol=self.random_symbol,
                    percentage=self.random_percentage,
                    shifts=self.random_shifts,
                    confidence_level=self.random_confidence,
                    export_target=self.random_export_target
                )
            else:
                self.fail("Evaluator missing evaluate_stress or execute method")

            mock_pipeline_cls.assert_called_with(self.random_storage_file)
            mock_pipeline_instance.execute.assert_called_with(
                self.random_symbol,
                self.random_percentage,
                self.random_shifts
            )

            self.assertIsInstance(result, dict)
            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.random_portfolio_id)
            self.assertIn("aggregate_loss", result)
            expected_aggregate = mock_var_loss + mock_stress_loss
            self.assertAlmostEqual(result["aggregate_loss"], expected_aggregate, delta=0.01)

    def test_top_level_evaluate_portfolio_liquidity_stress_function(self):
        if not hasattr(evaluator_module, "evaluate_portfolio_liquidity_stress"):
            self.skipTest("Helper function evaluate_portfolio_liquidity_stress not exposed")

        mock_var_loss = round(random.uniform(500.0, 10000.0), 2)
        mock_stress_loss = round(random.uniform(20000.0, 80000.0), 2)
        token_id = "token-" + uuid.uuid4().hex

        with patch("skills.market_portfolio_liquidity_stress_evaluator.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_liquidity_stress_evaluator.market_portfolio_var_liquidity_core") as mock_var_core:

            mock_pipeline_inst = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_inst
            mock_pipeline_inst.execute.return_value = {
                "scenario_loss": mock_stress_loss,
                "token": token_id
            }

            mock_var_core.calculate_var_and_liquidity.return_value = {
                "var_loss": mock_var_loss,
                "token": token_id
            }
            if hasattr(mock_var_core, "market_portfolio_var_liquidity_core"):
                mock_var_instance = MagicMock()
                mock_var_instance.calculate_var_and_liquidity.return_value = {
                    "var_loss": mock_var_loss,
                    "token": token_id
                }
                mock_var_core.market_portfolio_var_liquidity_core.return_value = mock_var_instance

            res = evaluator_module.evaluate_portfolio_liquidity_stress(
                portfolio_id=self.random_portfolio_id,
                symbol=self.random_symbol,
                percentage=self.random_percentage,
                shifts=self.random_shifts,
                confidence_level=self.random_confidence,
                storage_file=self.random_storage_file,
                export_target=self.random_export_target
            )

            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("portfolio_id"), self.random_portfolio_id)
            total_loss = res.get("aggregate_loss", res.get("total_loss"))
            self.assertIsNotNone(total_loss)
            self.assertAlmostEqual(total_loss, mock_var_loss + mock_stress_loss, delta=0.01)

    def test_pipeline_execution_failure_propagates_or_reports_error(self):
        EvaluatorClass = self._get_target_class()
        unique_error_msg = "CriticalShockFailure_" + uuid.uuid4().hex

        with patch("skills.market_portfolio_liquidity_stress_evaluator.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_liquidity_stress_evaluator.market_portfolio_var_liquidity_core") as mock_var_core:

            mock_pipeline_inst = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_inst
            mock_pipeline_inst.execute.side_effect = RuntimeError(unique_error_msg)

            evaluator = EvaluatorClass(storage_file=self.random_storage_file)
            method = getattr(evaluator, "evaluate_stress", getattr(evaluator, "execute", None))

            try:
                result = method(
                    portfolio_id=self.random_portfolio_id,
                    symbol=self.random_symbol,
                    percentage=self.random_percentage,
                    shifts=self.random_shifts,
                    confidence_level=self.random_confidence,
                    export_target=self.random_export_target
                )
                self.assertIn("error", result)
                self.assertIn(unique_error_msg, str(result["error"]))
            except RuntimeError as ex:
                self.assertIn(unique_error_msg, str(ex))

    def test_var_liquidity_failure_handling(self):
        EvaluatorClass = self._get_target_class()
        unique_var_error = "VarCalculationFault_" + uuid.uuid4().hex

        with patch("skills.market_portfolio_liquidity_stress_evaluator.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_liquidity_stress_evaluator.market_portfolio_var_liquidity_core") as mock_var_core:

            mock_pipeline_inst = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_inst
            mock_pipeline_inst.execute.return_value = {"projected_loss": random.uniform(10.0, 50.0)}

            mock_var_core.calculate_var_and_liquidity.side_effect = ValueError(unique_var_error)
            if hasattr(mock_var_core, "market_portfolio_var_liquidity_core"):
                mock_var_inst = MagicMock()
                mock_var_inst.calculate_var_and_liquidity.side_effect = ValueError(unique_var_error)
                mock_var_core.market_portfolio_var_liquidity_core.return_value = mock_var_inst

            evaluator = EvaluatorClass(storage_file=self.random_storage_file)
            method = getattr(evaluator, "evaluate_stress", getattr(evaluator, "execute", None))

            try:
                result = method(
                    portfolio_id=self.random_portfolio_id,
                    symbol=self.random_symbol,
                    percentage=self.random_percentage,
                    shifts=self.random_shifts,
                    confidence_level=self.random_confidence,
                    export_target=self.random_export_target
                )
                self.assertIn("error", result)
                self.assertIn(unique_var_error, str(result["error"]))
            except ValueError as ex:
                self.assertIn(unique_var_error, str(ex))

    def test_stream_io_fallback_verification(self):
        EvaluatorClass = self._get_target_class()
        binary_noise = f"RANDOM_STREAM_{uuid.uuid4().hex}".encode("utf-8")
        stream_mock = io.BytesIO(binary_noise)

        with patch("skills.market_portfolio_liquidity_stress_evaluator.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_liquidity_stress_evaluator.market_portfolio_var_liquidity_core") as mock_var_core:

            mock_pipeline_inst = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_inst
            mock_pipeline_inst.execute.return_value = {"projected_loss": 100.0}

            mock_var_core.calculate_var_and_liquidity.return_value = {"var_value": 50.0}
            if hasattr(mock_var_core, "market_portfolio_var_liquidity_core"):
                inst = MagicMock()
                inst.calculate_var_and_liquidity.return_value = {"var_value": 50.0}
                mock_var_core.market_portfolio_var_liquidity_core.return_value = inst

            evaluator = EvaluatorClass(storage_file=self.random_storage_file)
            if hasattr(evaluator, "load_from_stream"):
                evaluator.load_from_stream(stream_mock)
                self.assertEqual(stream_mock.tell(), len(binary_noise))


if __name__ == "__main__":
    unittest.main()