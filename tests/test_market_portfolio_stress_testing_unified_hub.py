import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
import os

from skills.market_portfolio_stress_testing_unified_hub import (
    MarketPortfolioStressTestingUnifiedHub,
    market_portfolio_stress_testing_unified_hub
)

class TestMarketPortfolioStressTestingUnifiedHub(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.iterations = random.randint(100, 5000)
        self.scenario_code = uuid.uuid4().hex
        self.matrix_id = uuid.uuid4().hex
        self.risk_tolerance = round(random.uniform(0.01, 0.5), 4)
        self.threshold = round(random.uniform(0.05, 0.95), 4)

        self.mock_db = MagicMock()
        self.mock_mc_engine = MagicMock()
        self.mock_scenario_pipeline = MagicMock()
        self.mock_reporter = MagicMock()
        self.mock_var_core = MagicMock()
        self.mock_matrix_evaluator = MagicMock()
        self.mock_audit_exporter = MagicMock()
        self.mock_rebalance_trigger = MagicMock()

        self.hub = MarketPortfolioStressTestingUnifiedHub(
            db_storage=self.mock_db,
            market_portfolio_stress_monte_carlo_engine=self.mock_mc_engine,
            market_portfolio_stress_scenario_pipeline=self.mock_scenario_pipeline,
            market_portfolio_stress_reporter=self.mock_reporter,
            market_portfolio_var_liquidity_core=self.mock_var_core,
            market_portfolio_stress_scenario_matrix_evaluator=self.mock_matrix_evaluator,
            market_portfolio_audit_log_exporter=self.mock_audit_exporter,
            market_portfolio_stress_auto_rebalance_trigger=self.mock_rebalance_trigger
        )

    def test_execute_stress_testing_pipeline(self):
        expected_mc_res = {"simulation": uuid.uuid4().hex, "val": random.random()}
        expected_sc_res = {"scenario": uuid.uuid4().hex, "impact": random.random()}
        expected_report_id = uuid.uuid4().hex

        self.mock_mc_engine.run.return_value = expected_mc_res
        self.mock_scenario_pipeline.execute.return_value = expected_sc_res
        self.mock_reporter.generate.return_value = expected_report_id

        res = self.hub.execute_stress_testing_pipeline(
            self.portfolio_id, self.iterations, self.scenario_code
        )

        self.mock_mc_engine.run.assert_called_once_with(self.portfolio_id, self.iterations)
        self.mock_scenario_pipeline.execute.assert_called_once_with(self.portfolio_id, self.scenario_code)
        self.mock_reporter.generate.assert_called_once_with({
            "portfolio_id": self.portfolio_id,
            "monte_carlo": expected_mc_res,
            "scenario": expected_sc_res
        })

        self.assertEqual(res["monte_carlo"], expected_mc_res)
        self.assertEqual(res["scenario"], expected_sc_res)
        self.assertEqual(res["report_id"], expected_report_id)

    def test_aggregate_metrics_stream(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)
        expected_calc_res = {"var": random.random(), "liquidity": random.randint(1000, 99999)}
        self.mock_var_core.calculate.return_value = expected_calc_res

        res = self.hub.aggregate_metrics_stream(mock_stream)

        self.mock_var_core.calculate.assert_called_once_with(random_bytes)
        self.assertEqual(res, expected_calc_res)

    def test_evaluate_and_trigger_rebalance_when_true(self):
        self.mock_rebalance_trigger.evaluate.return_value = True
        expected_exec_res = {"status": "rebalanced", "id": uuid.uuid4().hex}
        self.mock_rebalance_trigger.execute.return_value = expected_exec_res

        res = self.hub.evaluate_and_trigger_rebalance(self.portfolio_id, self.threshold)

        self.mock_rebalance_trigger.evaluate.assert_called_once_with(self.portfolio_id, self.threshold)
        self.mock_rebalance_trigger.execute.assert_called_once_with(self.portfolio_id)
        self.assertEqual(res, expected_exec_res)

    def test_evaluate_and_trigger_rebalance_when_false(self):
        self.mock_rebalance_trigger.evaluate.return_value = False

        res = self.hub.evaluate_and_trigger_rebalance(self.portfolio_id, self.threshold)

        self.mock_rebalance_trigger.evaluate.assert_called_once_with(self.portfolio_id, self.threshold)
        self.mock_rebalance_trigger.execute.assert_not_called()
        self.assertIsNone(res)

    def test_export_stress_audit_logs(self):
        export_target = uuid.uuid4().hex
        expected_export_res = {"exported_records": random.randint(10, 500)}
        self.mock_audit_exporter.export.return_value = expected_export_res

        res = self.hub.export_stress_audit_logs(export_target)

        self.mock_audit_exporter.export.assert_called_once_with(export_target)
        self.assertEqual(res, expected_export_res)

    def test_run_scenario_matrix(self):
        expected_matrix_res = {"matrix_id": self.matrix_id, "score": random.random()}
        self.mock_matrix_evaluator.evaluate_matrix.return_value = expected_matrix_res

        res = self.hub.run_scenario_matrix(self.matrix_id, self.risk_tolerance)

        self.mock_matrix_evaluator.evaluate_matrix.assert_called_once_with(self.matrix_id, self.risk_tolerance)
        self.assertEqual(res, expected_matrix_res)

    def test_functional_helper_without_file(self):
        mc_data = {"val": uuid.uuid4().hex}
        sc_data = {"res": uuid.uuid4().hex}
        payload = {
            "portfolio_id": self.portfolio_id,
            "monte_carlo": mc_data,
            "scenarios": sc_data
        }

        response = market_portfolio_stress_testing_unified_hub(payload)

        self.assertTrue(response["success"])
        self.assertEqual(response["portfolio_id"], self.portfolio_id)
        self.assertEqual(response["monte_carlo"], mc_data)
        self.assertEqual(response["scenarios"], sc_data)
        self.assertNotIn("output_file", response)

    def test_functional_helper_with_file(self):
        output_file = f"{uuid.uuid4().hex}.json"
        mc_data = {"val": uuid.uuid4().hex}
        sc_data = {"res": uuid.uuid4().hex}
        payload = {
            "portfolio_id": self.portfolio_id,
            "output_file": output_file,
            "monte_carlo": mc_data,
            "scenarios": sc_data
        }

        try:
            response = market_portfolio_stress_testing_unified_hub(payload)

            self.assertTrue(response["success"])
            self.assertEqual(response["output_file"], output_file)
            self.assertTrue(os.path.exists(output_file))

            with open(output_file, "r", encoding="utf-8") as f:
                file_data = json.load(f)

            self.assertEqual(file_data["portfolio_id"], self.portfolio_id)
            self.assertEqual(file_data["monte_carlo"], mc_data)
            self.assertEqual(file_data["scenarios"], sc_data)
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)