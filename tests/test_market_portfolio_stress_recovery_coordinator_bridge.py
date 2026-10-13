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
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM{uuid.uuid4().hex[:4].upper()}"
        self.url = f"https://api.{uuid.uuid4().hex[:6]}.com/webhook"
        self.telegram_token = f"{random.randint(1000, 9999)}:ABC{uuid.uuid4().hex[:8]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.percentage = round(random.uniform(5.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_init_creates_storage_if_missing(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_execute_recovery_workflow_success(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        
        mock_stress_res = {"status": "success", "detail": uuid.uuid4().hex}
        mock_rec_res = {"status": "success", "info": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             with_patch_recovery := patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipe:
            
            mock_pipeline_instance = mock_pipeline_cls.return_value
            mock_pipeline_instance.execute.return_value = mock_stress_res
            mock_run_pipe.return_value = mock_rec_res

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
            self.assertEqual(res["stress_result"]["detail"], mock_stress_res["detail"])
            self.assertEqual(res["recovery_result"]["result"], mock_rec_res)

            with open(self.storage_file, "r") as f:
                saved_data = json.load(f)
            self.assertIn(self.symbol, saved_data)
            self.assertEqual(saved_data[self.symbol]["percentage"], self.percentage)
            self.assertEqual(saved_data[self.symbol]["shifts"], self.shifts)
            self.assertEqual(saved_data[self.symbol]["status"], "workflow_run")

    def test_execute_recovery_workflow_exceptions_fallback(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipe:
            
            mock_pipeline_instance = mock_pipeline_cls.return_value
            mock_pipeline_instance.execute.side_effect = Exception(uuid.uuid4().hex)
            mock_run_pipe.side_effect = Exception(uuid.uuid4().hex)

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

    def test_run_stress_recovery_coordinator_success(self):
        mock_stress_output = {"data": uuid.uuid4().hex}
        mock_monitor_output = {"data": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
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
            self.assertEqual(res["stress"]["data"], mock_stress_output["data"])
            self.assertEqual(res["recovery"]["result"], mock_monitor_output)

            with open(self.storage_file, "r") as f:
                saved_data = json.load(f)
            self.assertEqual(saved_data[self.symbol]["status"], "coordinator_run")

    def test_run_stress_recovery_coordinator_exceptions(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
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
            self.assertEqual(res["stress"]["shifts"], self.shifts)
            self.assertEqual(res["recovery"]["status"], "failed")

    def test_run_stress_recovery_coordinator_pipeline_success(self):
        mock_stress_res = {"output": uuid.uuid4().hex}
        mock_recovery_res = {"output": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.return_value = mock_stress_res
            mock_start_new.return_value = mock_recovery_res

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
            self.assertEqual(res["stress"]["symbol"], self.symbol)
            self.assertEqual(res["stress"]["output"], mock_stress_res["output"])
            self.assertEqual(res["recovery"]["result"], mock_recovery_res)

            with open(self.storage_file, "r") as f:
                saved_data = json.load(f)
            self.assertEqual(saved_data[self.symbol]["price"], self.price)
            self.assertEqual(saved_data[self.symbol]["status"], "pipeline_run")

    def test_run_stress_recovery_coordinator_pipeline_exceptions(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.side_effect = ValueError(uuid.uuid4().hex)
            mock_start_new.side_effect = ValueError(uuid.uuid4().hex)

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

            self.assertEqual(res["stress"]["status"], "simulated")
            self.assertEqual(res["stress"]["symbol"], self.symbol)
            self.assertEqual(res["recovery"]["status"], "failed")

if __name__ == "__main__":
    unittest.main()