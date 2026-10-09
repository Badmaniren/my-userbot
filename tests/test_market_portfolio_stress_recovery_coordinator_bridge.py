import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import tempfile
import io

from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestStressRecoveryCoordinatorBridge(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.db")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.test/webhook"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC-{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bridge_initialization_creates_file(self):
        non_existent_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.db")
        self.assertFalse(os.path.exists(non_existent_path))
        bridge = StressRecoveryCoordinatorBridge(storage_file=non_existent_path)
        self.assertTrue(os.path.exists(non_existent_path))
        with open(non_existent_path, "r") as f:
            content = f.read()
        self.assertEqual(json.loads(content), {})

    def test_execute_recovery_workflow_success(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:

            mock_pipeline_instance = mock_pipeline_cls.return_value
            expected_stress_output = {"status": "ok", "detail": uuid.uuid4().hex, "symbol": self.symbol}
            mock_pipeline_instance.execute.return_value = expected_stress_output

            expected_recovery_output = {"status": "recovered", "token": uuid.uuid4().hex}
            mock_run_pipeline.return_value = expected_recovery_output

            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_run_pipeline.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertIn("stress_result", result)
            self.assertIn("recovery_result", result)
            self.assertEqual(result["stress_result"]["symbol"], self.symbol)
            self.assertEqual(result["recovery_result"], expected_recovery_output)

            with open(self.storage_file, "r") as f:
                saved_data = json.load(f)
            self.assertIn(self.symbol, saved_data)
            self.assertEqual(saved_data[self.symbol]["percentage"], self.percentage)
            self.assertEqual(saved_data[self.symbol]["shifts"], self.shifts)
            self.assertEqual(saved_data[self.symbol]["status"], "workflow_run")

    def test_execute_recovery_workflow_pipeline_exception_fallback(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:

            mock_pipeline_instance = mock_pipeline_cls.return_value
            mock_pipeline_instance.execute.side_effect = Exception(uuid.uuid4().hex)

            err_msg = uuid.uuid4().hex
            mock_run_pipeline.side_effect = Exception(err_msg)

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
            self.assertEqual(result["recovery_result"]["error"], err_msg)

    def test_run_stress_recovery_coordinator(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:

            stress_return = {"metric": uuid.uuid4().hex}
            mock_run_stress.return_value = stress_return

            monitor_return = {"sentinel": uuid.uuid4().hex}
            mock_start_new.return_value = monitor_return

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"]["symbol"], self.symbol)
            self.assertEqual(result["recovery"], monitor_return)

            with open(self.storage_file, "r") as f:
                data = json.load(f)
            self.assertEqual(data[self.symbol]["status"], "coordinator_run")

    def test_run_stress_recovery_coordinator_exceptions(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:

            mock_run_stress.side_effect = ValueError(uuid.uuid4().hex)
            mock_start_new.side_effect = RuntimeError(uuid.uuid4().hex)

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(result["stress"]["status"], "simulated")
            self.assertEqual(result["stress"]["symbol"], self.symbol)
            self.assertEqual(result["stress"]["shifts"], self.shifts)

            self.assertEqual(result["recovery"]["status"], "failed")
            self.assertIn("error", result["recovery"])

    def test_run_stress_recovery_coordinator_pipeline(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:

            mock_run_stress.return_value = {"computed": True}
            mock_start_new.return_value = "non_dict_result"

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

            expected_shifts_list = list(range(self.shifts))
            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, expected_shifts_list)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"]["symbol"], self.symbol)
            self.assertEqual(result["recovery"]["status"], "success")
            self.assertEqual(result["recovery"]["result"], "non_dict_result")

            with open(self.storage_file, "r") as f:
                data = json.load(f)
            self.assertEqual(data[self.symbol]["price"], self.price)
            self.assertEqual(data[self.symbol]["status"], "pipeline_run")