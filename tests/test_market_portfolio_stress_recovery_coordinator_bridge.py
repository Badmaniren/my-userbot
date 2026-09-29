import os
import unittest
from unittest.mock import patch, MagicMock
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
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_class_execution_success(self):
        mock_stress_res = {"status": uuid.uuid4().hex, "metric": random.randint(1, 100)}
        mock_recovery_res = {"result": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as MockPipeline, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline', return_value=mock_recovery_res) as mock_run_pipeline:

            instance_pipeline_mock = MockPipeline.return_value
            instance_pipeline_mock.execute.return_value = mock_stress_res

            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertTrue(os.path.exists(self.storage_file))
            self.assertEqual(result["stress_result"], mock_stress_res)
            self.assertEqual(result["recovery_result"], mock_recovery_res)
            instance_pipeline_mock.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_run_pipeline.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

    def test_bridge_class_execution_key_error_fallback(self):
        mock_recovery_res = {"status": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as MockPipeline, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline', return_value=mock_recovery_res):

            instance_pipeline_mock = MockPipeline.return_value
            instance_pipeline_mock.execute.side_effect = KeyError("Simulated failure")

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
            self.assertEqual(result["recovery_result"], mock_recovery_res)

    def test_run_stress_recovery_coordinator_success(self):
        mock_stress_output = {"data": uuid.uuid4().hex}
        mock_monitor_output = {"monitor": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', return_value=mock_stress_output) as mock_stress_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value=mock_monitor_output) as mock_start_new:

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
            self.assertEqual(result["stress"], mock_stress_output)
            self.assertEqual(result["recovery"], mock_monitor_output)
            mock_stress_func.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

    def test_run_stress_recovery_coordinator_exception_fallback(self):
        mock_monitor_output = {"monitor_status": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', side_effect=TypeError("Type mismatch")) as mock_stress_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value=mock_monitor_output):

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
            self.assertEqual(result["recovery"], mock_monitor_output)

    def test_run_stress_recovery_coordinator_pipeline_success(self):
        mock_stress_result = {"pipeline_stress": uuid.uuid4().hex}
        mock_recovery_result = {"pipeline_recovery": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', return_value=mock_stress_result) as mock_pipeline_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value=mock_recovery_result) as mock_start_new:

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

            self.assertTrue(os.path.exists(self.storage_file))
            self.assertEqual(result["stress"], mock_stress_result)
            self.assertEqual(result["recovery"], mock_recovery_result)
            mock_pipeline_func.assert_called_once()
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

    def test_run_stress_recovery_coordinator_pipeline_iterable_shifts(self):
        custom_shifts = [random.randint(1, 10), random.randint(11, 20)]
        mock_stress_result = {"custom_shifts": True}
        mock_recovery_result = {"status": "ok"}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', return_value=mock_stress_result) as mock_pipeline_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value=mock_recovery_result):

            result = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=custom_shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            mock_pipeline_func.assert_called_once_with(self.storage_file, self.symbol, self.percentage, custom_shifts)
            self.assertEqual(result["stress"], mock_stress_result)

    def test_run_stress_recovery_coordinator_pipeline_key_error_fallback(self):
        custom_shifts = random.randint(1, 5)
        mock_recovery_result = {"active": False}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', side_effect=KeyError("Missing key")) as mock_pipeline_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value=mock_recovery_result):

            result = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=custom_shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            self.assertEqual(result["stress"]["status"], "simulated")
            self.assertEqual(result["stress"]["symbol"], self.symbol)
            self.assertEqual(result["stress"]["shifts"], list(range(custom_shifts)))
            self.assertEqual(result["recovery"], mock_recovery_result)

if __name__ == '__main__':
    unittest.main()