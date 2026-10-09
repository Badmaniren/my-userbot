import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import tempfile
import shutil

from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestStressRecoveryCoordinatorBridge(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.org/webhook"
        self.telegram_token = f"bot{uuid.uuid4().hex}:{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.percentage = random.uniform(0.05, 0.95)
        self.shifts = random.randint(2, 8)
        self.price = random.uniform(100.0, 1500.0)
        self.storage_file = os.path.join(self.temp_dir, f"storage_{uuid.uuid4().hex}.db")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_bridge_initialization_and_successful_workflow(self):
        random_stress_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_recovery_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.execute.return_value = random_stress_output
            mock_pipeline_cls.return_value = mock_pipeline_instance
            mock_run_pipeline.return_value = random_recovery_output

            bridge = StressRecoveryCoordinatorBridge(self.storage_file)
            
            self.assertTrue(os.path.exists(self.storage_file))
            with open(self.storage_file, "r") as f:
                self.assertEqual(f.read(), "{}")

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
            
            self.assertEqual(result["stress_result"], random_stress_output)
            self.assertEqual(result["recovery_result"], random_recovery_output)

    def test_bridge_workflow_fallback_on_exception(self):
        random_recovery_non_dict = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_cls, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.execute.side_effect = KeyError("Simulated KeyError")
            mock_pipeline_cls.return_value = mock_pipeline_instance
            mock_run_pipeline.return_value = random_recovery_non_dict

            bridge = StressRecoveryCoordinatorBridge(self.storage_file)
            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            expected_stress_fallback = {
                "status": "simulated",
                "symbol": self.symbol,
                "percentage": self.percentage
            }
            expected_recovery_fallback = {
                "status": "success",
                "result": random_recovery_non_dict
            }

            self.assertEqual(result["stress_result"], expected_stress_fallback)
            self.assertEqual(result["recovery_result"], expected_recovery_fallback)

    def test_run_stress_recovery_coordinator_success(self):
        random_stress_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_monitor_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.return_value = random_stress_output
            mock_start_new.return_value = random_monitor_output

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertTrue(os.path.exists(self.storage_file))
            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)
            
            self.assertEqual(result["stress"], random_stress_output)
            self.assertEqual(result["recovery"], random_monitor_output)

    def test_run_stress_recovery_coordinator_fallback(self):
        random_monitor_non_dict = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.side_effect = TypeError("Simulated TypeError")
            mock_start_new.return_value = random_monitor_non_dict

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            expected_stress_fallback = {
                "status": "simulated",
                "symbol": self.symbol,
                "shifts": self.shifts
            }
            expected_recovery_fallback = {
                "status": "success",
                "result": random_monitor_non_dict
            }

            self.assertEqual(result["stress"], expected_stress_fallback)
            self.assertEqual(result["recovery"], expected_recovery_fallback)

    def test_run_stress_recovery_coordinator_pipeline_success(self):
        random_stress_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_recovery_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.return_value = random_stress_output
            mock_start_new.return_value = random_recovery_output

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

            expected_shifts_arg = list(range(self.shifts))
            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, expected_shifts_arg)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"], random_stress_output)
            self.assertEqual(result["recovery"], random_recovery_output)

    def test_run_stress_recovery_coordinator_pipeline_fallback(self):
        random_recovery_non_dict = uuid.uuid4().hex
        custom_shifts_list = [random.randint(1, 5), random.randint(6, 10)]

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.side_effect = KeyError("Simulated KeyError")
            mock_start_new.return_value = random_recovery_non_dict

            result = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=custom_shifts_list,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            expected_stress_fallback = {
                "status": "simulated",
                "symbol": self.symbol,
                "shifts": custom_shifts_list
            }
            expected_recovery_fallback = {
                "status": "success",
                "result": random_recovery_non_dict
            }

            self.assertEqual(result["stress"], expected_stress_fallback)
            self.assertEqual(result["recovery"], expected_recovery_fallback)

if __name__ == "__main__":
    unittest.main()