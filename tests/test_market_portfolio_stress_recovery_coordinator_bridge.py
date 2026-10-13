import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import io

from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestStressRecoveryCoordinatorBridge(unittest.TestCase):
    
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_initialization_creates_storage(self):
        self.assertFalse(os.path.exists(self.storage_file))
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline:
            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            mock_pipeline.assert_called_once_with(self.storage_file)
        
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r") as f:
            content = json.load(f)
        self.assertEqual(content, {})

    def test_execute_recovery_workflow_success(self):
        mock_stress_res = {"status": "ok", "detail": uuid.uuid4().hex}
        mock_recovery_res = {"status": "active", "id": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            instance_mock = mock_pipeline_cls.return_value
            instance_mock.execute.return_value = mock_stress_res
            mock_run_pipeline.return_value = mock_recovery_res

            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertIn("stress_result", result)
            self.assertIn("recovery_result", result)
            self.assertEqual(result["stress_result"]["symbol"], self.symbol)
            self.assertEqual(result["stress_result"]["detail"], mock_stress_res["detail"])
            self.assertEqual(result["recovery_result"], mock_recovery_res)

            with open(self.storage_file, "r") as f:
                data = json.load(f)
            self.assertIn(self.symbol, data)
            self.assertEqual(data[self.symbol]["percentage"], self.percentage)
            self.assertEqual(data[self.symbol]["shifts"], self.shifts)
            self.assertEqual(data[self.symbol]["status"], "workflow_run")

    def test_execute_recovery_workflow_exceptions_fallback(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            instance_mock = mock_pipeline_cls.return_value
            instance_mock.execute.side_effect = Exception("Stress failure")
            mock_run_pipeline.side_effect = Exception("Recovery failure")

            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(result["stress_result"]["status"], "simulated")
            self.assertEqual(result["stress_result"]["symbol"], self.symbol)
            self.assertEqual(result["stress_result"]["percentage"], self.percentage)
            
            self.assertEqual(result["recovery_result"]["status"], "failed")
            self.assertIn("Recovery failure", result["recovery_result"]["error"])

    def test_run_stress_recovery_coordinator_success(self):
        mock_stress_output = {"custom_metric": uuid.uuid4().hex}
        mock_monitor_output = {"monitor_id": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_stress_fn, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_stress_fn.return_value = mock_stress_output
            mock_start_new.return_value = mock_monitor_output

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertIn("stress", result)
            self.assertIn("recovery", result)
            self.assertEqual(result["stress"]["symbol"], self.symbol)
            self.assertEqual(result["stress"]["custom_metric"], mock_stress_output["custom_metric"])
            self.assertEqual(result["recovery"], mock_monitor_output)

            with open(self.storage_file, "r") as f:
                data = json.load(f)
            self.assertEqual(data[self.symbol]["status"], "coordinator_run")

    def test_run_stress_recovery_coordinator_pipeline_flow(self):
        mock_stress_res = uuid.uuid4().hex
        mock_monitor_res = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_stress_fn, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_stress_fn.return_value = mock_stress_res
            mock_start_new.return_value = mock_monitor_res

            result = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=self.shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            self.assertEqual(result["stress"]["status"], "success")
            self.assertEqual(result["stress"]["result"], mock_stress_res)
            self.assertEqual(result["stress"]["symbol"], self.symbol)

            self.assertEqual(result["recovery"]["status"], "success")
            self.assertEqual(result["recovery"]["result"], mock_monitor_res)

            with open(self.storage_file, "r") as f:
                data = json.load(f)
            self.assertEqual(data[self.symbol]["price"], self.price)
            self.assertEqual(data[self.symbol]["status"], "pipeline_run")

    def test_non_integer_shifts_in_pipeline(self):
        custom_shifts_list = [random.randint(1, 10), random.randint(11, 20)]

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_stress_fn, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_stress_fn.return_value = {"status": "ok", "symbol": self.symbol}
            mock_start_new.return_value = {"status": "ok"}

            run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=custom_shifts_list,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            mock_stress_fn.assert_called_once_with(
                self.storage_file,
                self.symbol,
                self.percentage,
                custom_shifts_list
            )