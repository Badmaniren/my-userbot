import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import string
from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestStressRecoveryCoordinatorBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/webhook"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_initialization_creates_file(self):
        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as mock_pipeline:
            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            self.assertTrue(os.path.exists(self.storage_file))
            with open(self.storage_file, "r") as f:
                content = json.load(f)
            self.assertEqual(content, {})
            mock_pipeline.assert_called_once_with(self.storage_file)

    def test_execute_recovery_workflow_success(self):
        mock_stress_output = {"status": "executed", "details": uuid.uuid4().hex}
        mock_recovery_output = {"status": "recovered", "token": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as MockPipelineClass, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline') as mock_run_pipeline:
            
            instance = MockPipelineClass.return_value
            instance.execute.return_value = mock_stress_output
            mock_run_pipeline.return_value = mock_recovery_output

            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            res = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertIn("stress_result", res)
            self.assertIn("recovery_result", res)
            self.assertEqual(res["stress_result"]["symbol"], self.symbol)
            self.assertEqual(res["stress_result"]["details"], mock_stress_output["details"])
            self.assertEqual(res["recovery_result"], mock_recovery_output)

            with open(self.storage_file, "r") as f:
                stored_data = json.load(f)
            self.assertIn(self.symbol, stored_data)
            self.assertEqual(stored_data[self.symbol]["percentage"], self.percentage)
            self.assertEqual(stored_data[self.symbol]["shifts"], self.shifts)
            self.assertEqual(stored_data[self.symbol]["status"], "workflow_run")

    def test_execute_recovery_workflow_exceptions_fallback(self):
        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as MockPipelineClass, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline') as mock_run_pipeline:
            
            instance = MockPipelineClass.return_value
            instance.execute.side_effect = Exception(uuid.uuid4().hex)
            mock_run_pipeline.side_effect = Exception(uuid.uuid4().hex)

            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            res = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(res["stress_result"]["status"], "simulated")
            self.assertEqual(res["stress_result"]["symbol"], self.symbol)
            self.assertEqual(res["stress_result"]["percentage"], self.percentage)
            self.assertEqual(res["recovery_result"]["status"], "failed")
            self.assertIn("error", res["recovery_result"])

    def test_run_stress_recovery_coordinator(self):
        mock_stress_output = {"market_metric": uuid.uuid4().hex}
        mock_monitor_output = {"monitor_status": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:
            
            mock_run_stress.return_value = mock_stress_output
            mock_start_new.return_value = mock_monitor_output

            res = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertIn("stress", res)
            self.assertIn("recovery", res)
            self.assertEqual(res["stress"]["symbol"], self.symbol)
            self.assertEqual(res["stress"]["market_metric"], mock_stress_output["market_metric"])
            self.assertEqual(res["recovery"], mock_monitor_output)

            with open(self.storage_file, "r") as f:
                stored_data = json.load(f)
            self.assertEqual(stored_data[self.symbol]["status"], "coordinator_run")

    def test_run_stress_recovery_coordinator_exceptions(self):
        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:
            
            mock_run_stress.side_effect = RuntimeError(uuid.uuid4().hex)
            mock_start_new.side_effect = RuntimeError(uuid.uuid4().hex)

            res = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(res["stress"]["status"], "simulated")
            self.assertEqual(res["stress"]["symbol"], self.symbol)
            self.assertEqual(res["recovery"]["status"], "failed")

    def test_run_stress_recovery_coordinator_pipeline(self):
        mock_stress_output = {"pipeline_code": uuid.uuid4().hex}
        mock_recovery_output = "raw_string_result"

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:
            
            mock_run_stress.return_value = mock_stress_output
            mock_start_new.return_value = mock_recovery_output

            res = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=self.shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            self.assertIn("stress", res)
            self.assertIn("recovery", res)
            self.assertEqual(res["stress"]["pipeline_code"], mock_stress_output["pipeline_code"])
            self.assertEqual(res["recovery"], {"status": "success", "result": "raw_string_result"})

            with open(self.storage_file, "r") as f:
                stored_data = json.load(f)
            self.assertEqual(stored_data[self.symbol]["price"], self.price)
            self.assertEqual(stored_data[self.symbol]["status"], "pipeline_run")

    def test_run_stress_recovery_coordinator_pipeline_with_list_shifts(self):
        custom_shifts = [random.randint(1, 5), random.randint(6, 10)]
        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:
            
            mock_run_stress.return_value = {"status": "ok"}
            mock_start_new.return_value = {"status": "ok"}

            run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=custom_shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, custom_shifts)

if __name__ == '__main__':
    unittest.main()