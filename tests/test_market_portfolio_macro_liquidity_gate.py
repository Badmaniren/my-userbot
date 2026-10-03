import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.market_portfolio_macro_liquidity_gate import MacroLiquidityGate, market_portfolio_macro_liquidity_gate

class TestMarketPortfolioMacroLiquidityGate(unittest.TestCase):
    def test_aggregate_macro_liquidity_success(self):
        portfolio_id = uuid.uuid4().hex
        mock_db = MagicMock()
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = {uuid.uuid4().hex: random.uniform(10.0, 100.0)}
        mock_var_core = MagicMock()
        mock_var_core.calculate.return_value = random.uniform(1.0, 50.0)

        gate = MacroLiquidityGate(
            db_storage=mock_db,
            extractor_tool_1790087207=mock_extractor,
            market_portfolio_var_liquidity_core=mock_var_core
        )

        result = gate.aggregate_macro_liquidity(portfolio_id)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("macro_liquidity_score", result)
        self.assertIn("details", result)
        mock_db.save.assert_called_once()

    def test_aggregate_macro_liquidity_exception(self):
        portfolio_id = uuid.uuid4().hex
        mock_notifier = MagicMock()
        mock_extractor = MagicMock()
        error_message = uuid.uuid4().hex
        mock_extractor.extract.side_effect = Exception(error_message)

        gate = MacroLiquidityGate(
            extractor_tool_1790087207=mock_extractor,
            market_portfolio_audit_alert_notifier=mock_notifier
        )

        with self.assertRaises(Exception):
            gate.aggregate_macro_liquidity(portfolio_id)

        mock_notifier.notify_error.assert_called_once_with(error_message)

    def test_process_external_stream(self):
        stream_id = uuid.uuid4().hex
        mock_parser = MagicMock()
        parsed_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_parser.parse_stream.return_value = parsed_result

        gate = MacroLiquidityGate(market_parser=mock_parser)

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raw = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
            mock_get.return_value = mock_response

            res = gate.process_external_stream(stream_id)

            self.assertEqual(res["status"], "success")
            self.assertEqual(res["stream_id"], stream_id)
            self.assertEqual(res["parsed"], parsed_result)
            mock_get.assert_called_once_with(f"http://example.com/stream/{stream_id}")

    def test_run_liquidity_scenario(self):
        scenario_id = uuid.uuid4().hex
        shock = random.uniform(-1.0, 1.0)
        mock_scenario = MagicMock()
        simulation_result = {uuid.uuid4().hex: random.random()}
        mock_scenario.simulate.return_value = simulation_result
        mock_simulator = MagicMock()

        gate = MacroLiquidityGate(
            market_portfolio_liquidity_scenario_analyzer=mock_scenario,
            market_portfolio_scenario_simulator=mock_simulator
        )

        res = gate.run_liquidity_scenario(scenario_id, shock)

        self.assertEqual(res, simulation_result)
        mock_scenario.simulate.assert_called_once_with(scenario_id, shock)
        mock_simulator.record.assert_called_once_with(simulation_result)

    def test_functional_gate_handler(self):
        portfolio_id = uuid.uuid4().hex
        base_liquidity = random.uniform(100.0, 1000.0)
        macro_factor = random.uniform(10.0, 100.0)
        input_data = {
            "portfolio_id": portfolio_id,
            "liquidity_data": {"base_liquidity": base_liquidity},
            "macro_factor": macro_factor
        }

        output = market_portfolio_macro_liquidity_gate(input_data)

        self.assertEqual(output["portfolio_id"], portfolio_id)
        self.assertEqual(output["macro_factor"], macro_factor)
        self.assertEqual(output["aggregated_score"], base_liquidity + macro_factor)
        self.assertEqual(output["liquidity_data"], input_data["liquidity_data"])

if __name__ == "__main__":
    unittest.main()