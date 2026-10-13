import os
import json
import uuid
import random
import string
import unittest
from unittest.mock import patch, MagicMock
import io

from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)


class TestMarketPortfolioStressRecoveryCoordinatorBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_recovery_{uuid.uuid4().hex}.db"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        # ИСПРАВЛЕНИЕ ОШИБКИ: uuid.uuid4().int — это число, берем по модулю или через hex для генерации строки
        self.chat_id = str(uuid.uuid4().int % 1000000000)
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_init_creates_storage(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r") as f:
            content = json.load(f)
        self.assertEqual(content, {})

    def test_execute_recovery_workflow_success(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)

        mock_stress_res = {"status": "success", "detail": uuid.uuid4().hex}
        mock_recovery_res = {"status": "success", "id": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as MockPipelineClass, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            instance = MockPipelineClass.return_value
            instance.execute.return_value = mock_stress_res
            mock_run_pipeline.return_value = mock_recovery_res

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
            self.assertEqual(res["recovery_result"], mock_recovery_res)

            with open(self.storage_file, "r") as f:
                data = json.load(f)
            self.assertIn(self.symbol, data)
            self.assertEqual(data[self.symbol]["percentage"], self.percentage)
            self.assertEqual(data[self.symbol]["shifts"], self.shifts)

    def test_execute_recovery_workflow_exceptions_fallback(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as MockPipelineClass, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            instance = MockPipelineClass.return_value
            instance.execute.side_effect = Exception(uuid.uuid4().hex)
            mock_run_pipeline.side_effect = Exception(uuid.uuid4().hex)

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
            self.assertEqual(res["recovery_result"]["status"], "failed")

    def test_run_stress_recovery_coordinator_success(self):
        mock_stress_out = {"data": uuid.uuid4().hex}
        mock_monitor_out = {"active": True}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_stress_func, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_stress_func.return_value = mock_stress_out
            mock_start_new.return_value = mock_monitor_out

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
            self.assertEqual(res["recovery"], mock_monitor_out)

            with open(self.storage_file, "r") as f:
                data = json.load(f)
            self.assertEqual(data[self.symbol]["status"], "coordinator_run")

    def test_run_stress_recovery_coordinator_exceptions(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_stress_func, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_stress_func.side_effect = ValueError(uuid.uuid4().hex)
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

    def test_run_stress_recovery_coordinator_pipeline_success(self):
        mock_stress_res = {"executed": True}
        mock_recovery_res = io.BytesIO(b"some_bytes")

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_stress_func, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_stress_func.return_value = mock_stress_res
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
            self.assertEqual(res["recovery"]["result"], mock_recovery_res)

            with open(self.storage_file, "r") as f:
                data = json.load(f)
            self.assertEqual(data[self.symbol]["price"], self.price)
            self.assertEqual(data[self.symbol]["status"], "pipeline_run")

    def test_run_stress_recovery_coordinator_pipeline_non_int_shifts(self):
        non_int_shifts = [random.randint(1, 5), random.randint(6, 10)]

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_stress_func, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_stress_func.return_value = {"ok": True}
            mock_start_new.return_value = {"ok": True}

            res = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=non_int_shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            self.assertEqual(res["stress"]["symbol"], self.symbol)
            mock_stress_func.assert_called_once_with(
                self.storage_file, self.symbol, self.percentage, non_int_shifts
            )