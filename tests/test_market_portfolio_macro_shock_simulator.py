import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.market_portfolio_macro_shock_simulator import (
    MacroShockSimulator,
    market_portfolio_macro_shock_simulator
)

class TestMacroShockSimulator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.shock_type = random.choice(["inflation", "rate_hike", "liquidity_crunch", "currency_devaluation"])
        self.shock_magnitude = round(random.uniform(0.01, 0.5), 4)

    def test_macro_shock_simulator_init_and_single_simulate(self):
        mock_db = unittest.mock.MagicMock()
        mock_db.get_portfolio.return_value = {"portfolio_id": self.portfolio_id, "assets": []}

        mock_scenario = unittest.mock.MagicMock()
        expected_sim_result = {"status": "simulated", "loss": random.randint(100, 5000)}
        mock_scenario.run_scenario.return_value = expected_sim_result

        mock_dispatcher = unittest.mock.MagicMock()

        simulator = MacroShockSimulator(
            db_storage=mock_db,
            market_portfolio_scenario_simulator=mock_scenario,
            market_portfolio_alert_dispatcher=mock_dispatcher
        )

        result = simulator.simulate_shock(self.portfolio_id, self.shock_type, self.shock_magnitude)

        self.assertIn("event_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["shock_type"], self.shock_type)
        self.assertEqual(result["magnitude"], self.shock_magnitude)
        self.assertEqual(result["simulation_result"], expected_sim_result)

        mock_db.get_portfolio.assert_called_once_with(self.portfolio_id)
        mock_scenario.run_scenario.assert_called_once_with(self.portfolio_id, self.shock_type, self.shock_magnitude)
        mock_dispatcher.dispatch.assert_called_once()

    def test_simulate_shock_portfolio_not_found(self):
        mock_db = unittest.mock.MagicMock()
        mock_db.get_portfolio.return_value = None

        simulator = MacroShockSimulator(db_storage=mock_db)

        with self.assertRaises(ValueError):
            simulator.simulate_shock(self.portfolio_id, self.shock_type, self.shock_magnitude)

    def test_export_shock_report_stream(self):
        report_id = uuid.uuid4().hex
        mock_export_tool = unittest.mock.MagicMock()
        expected_stream = io.BytesIO(uuid.uuid4().bytes)
        mock_export_tool.generate_stream.return_value = expected_stream

        with patch("skills.market_portfolio_data_exporter.generate_stream", mock_export_tool.generate_stream):
            simulator = MacroShockSimulator()
            stream = simulator.export_shock_report(report_id)
            self.assertEqual(stream, expected_stream)
            mock_export_tool.generate_stream.assert_called_once_with(report_id)

    def test_batch_simulate(self):
        portfolio_ids = [uuid.uuid4().hex for _ in range(3)]
        mock_db = unittest.mock.MagicMock()
        mock_db.get_portfolio.return_value = {"active": True}

        mock_scenario = unittest.mock.MagicMock()
        mock_scenario.run_scenario.return_value = {"impact": random.random()}

        simulator = MacroShockSimulator(
            db_storage=mock_db,
            market_portfolio_scenario_simulator=mock_scenario
        )

        results = simulator.batch_simulate(portfolio_ids, self.shock_type, self.shock_magnitude)

        self.assertEqual(len(results), len(portfolio_ids))
        for res in results:
            self.assertIn(res["portfolio_id"], portfolio_ids)
            self.assertEqual(res["shock_type"], self.shock_type)
            self.assertEqual(res["magnitude"], self.shock_magnitude)
            self.assertIn("simulation_result", res)

    def test_market_portfolio_macro_shock_simulator_function(self):
        shock_id = f"shock_{uuid.uuid4().hex[:8]}"
        scenario_id = uuid.uuid4().hex

        assets = [
            {
                "asset_id": uuid.uuid4().hex,
                "ticker": f"TICK_{random.randint(100, 999)}",
                "current_price": round(random.uniform(10.0, 1000.0), 2),
                "volume": random.randint(1, 100)
            }
        ]

        inflation_val = round(random.uniform(0.01, 0.1), 3)
        rate_hike_val = random.randint(0, 100)

        payload = {
            "shock_id": shock_id,
            "portfolio_id": self.portfolio_id,
            "scenario_id": scenario_id,
            "assets": assets,
            "macro_variables": {
                "inflation_shock": inflation_val,
                "central_bank_rate_hike": rate_hike_val
            }
        }

        mock_db_func = unittest.mock.MagicMock()

        with patch("skills.db_storage.db_storage", mock_db_func):
            output = market_portfolio_macro_shock_simulator(payload)

            self.assertEqual(output["shock_id"], shock_id)
            self.assertEqual(output["portfolio_id"], self.portfolio_id)
            self.assertEqual(output["scenario_id"], scenario_id)
            self.assertEqual(len(output["impact_results"]), len(assets))

            res_asset = output["impact_results"][0]
            self.assertEqual(res_asset["asset_id"], assets[0]["asset_id"])
            self.assertEqual(res_asset["ticker"], assets[0]["ticker"])

            expected_factor = 1.0 - (inflation_val + (rate_hike_val / 1000.0))
            expected_valuation = (assets[0]["current_price"] * assets[0]["volume"]) * expected_factor
            self.assertAlmostEqual(res_asset["adjusted_valuation"], expected_valuation)

            mock_db_func.assert_called_once()
            called_arg = mock_db_func.call_args[0][0]
            self.assertEqual(called_arg["action"], "save_macro_simulation")
            self.assertEqual(called_arg["shock_id"], shock_id)
            self.assertEqual(called_arg["data"], output)

if __name__ == "__main__":
    unittest.main()