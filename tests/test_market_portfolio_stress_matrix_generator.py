import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_stress_matrix_generator import (
    generate_stress_matrix,
    export_matrix_data,
    execute_pipeline_check
)
import skills.market_portfolio_stress_matrix_generator as target_module

class TestMarketPortfolioStressMatrixGenerator(unittest.TestCase):

    def test_matrix_generation_logic_direct_execution(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_scenario_code = uuid.uuid4().hex
        rand_multiplier = random.uniform(0.1, 9.9)

        mock_db = MagicMock()
        mock_db.fetch_portfolio.return_value = {str(uuid.uuid4().hex): random.randint(1, 100)}

        mock_sim = MagicMock()
        mock_sim.simulate.return_value = {"multiplier": rand_multiplier}

        with patch.object(target_module, "db_storage", mock_db), \
             patch.object(target_module, "market_portfolio_scenario_simulator", mock_sim):

            res = generate_stress_matrix(rand_portfolio_id, simulation_data=rand_scenario_code)

            self.assertIn("matrix_id", res)
            self.assertEqual(res["portfolio_id"], rand_portfolio_id)
            self.assertEqual(res["scenario"], rand_scenario_code)
            self.assertEqual(res["result"], rand_multiplier)

    def test_matrix_generation_integration_style(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_sim_data = uuid.uuid4().hex
        rand_mc_data = uuid.uuid4().hex

        res = generate_stress_matrix(rand_portfolio_id, simulation_data=rand_sim_data, monte_carlo_data=rand_mc_data)

        self.assertIn("matrix_id", res)
        self.assertEqual(res["portfolio_id"], rand_portfolio_id)
        self.assertEqual(res["simulation_data"], rand_sim_data)
        self.assertEqual(res["monte_carlo_data"], rand_mc_data)
        self.assertEqual(res["matrix_data"]["status"], "GENERATED")
        self.assertTrue(res["persisted"])

    def test_stress_matrix_exception_handling(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_scenario_code = uuid.uuid4().hex

        mock_db = MagicMock()
        mock_sim = MagicMock()
        mock_sim.simulate.return_value = {"invalid_key": random.randint(1, 50)}

        with patch.object(target_module, "db_storage", mock_db), \
             patch.object(target_module, "market_portfolio_scenario_simulator", mock_sim):

            with self.assertRaises(ValueError) as ctx:
                generate_stress_matrix(rand_portfolio_id, simulation_data=rand_scenario_code)
            self.assertIn("Invalid simulation output", str(ctx.exception))

    def test_stress_matrix_stream_io_processing(self):
        rand_matrix_key = uuid.uuid4().hex
        rand_payload = uuid.uuid4().bytes

        mock_exporter = MagicMock()
        mock_exporter.export_stream.return_value = io.BytesIO(rand_payload)

        with patch.object(target_module, "market_portfolio_data_exporter", mock_exporter):
            content = export_matrix_data(rand_matrix_key)
            self.assertEqual(content, rand_payload)

    def test_stress_matrix_pipeline_integration(self):
        rand_p_id = uuid.uuid4().hex
        rand_th = random.uniform(0.01, 0.99)
        rand_pipeline_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_pipeline = MagicMock()
        mock_pipeline.run_pipeline.return_value = rand_pipeline_result

        with patch.object(target_module, "market_portfolio_stress_scenario_pipeline", mock_pipeline):
            result = execute_pipeline_check(rand_p_id, rand_th)
            mock_pipeline.run_pipeline.assert_called_once_with(rand_p_id, rand_th)
            self.assertEqual(result, rand_pipeline_result)

if __name__ == "__main__":
    unittest.main()