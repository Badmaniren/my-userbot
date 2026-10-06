import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_stress_hedge_controller import MarketPortfolioStressHedgeController

class TestMarketPortfolioStressHedgeController(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.threshold = round(random.uniform(0.01, 0.5), 4)
        self.event_id = f"ev_{uuid.uuid4().hex[:8]}"
        self.controller = MarketPortfolioStressHedgeController()

    def test_evaluate_stress_hedge_default(self):
        with patch.object(self.controller.scenario_pipeline, 'evaluate', return_value=True) as mock_eval:
            res = self.controller.evaluate_stress_hedge(self.portfolio_id, self.threshold)
            mock_eval.assert_called_once_with(self.portfolio_id, self.threshold)
            self.assertTrue(res)

    def test_evaluate_stress_hedge_with_matrix_evaluator(self):
        matrix_eval = MagicMock()
        expected_res = {"status": f"ok_{uuid.uuid4().hex[:4]}"}
        matrix_eval.evaluate.return_value = expected_res
        self.controller.market_portfolio_stress_scenario_matrix_evaluator = matrix_eval

        res = self.controller.evaluate_stress_hedge(self.portfolio_id, self.threshold)
        matrix_eval.evaluate.assert_called_once_with(self.portfolio_id, self.threshold)
        self.assertEqual(res, expected_res)

    def test_execute_auto_hedge(self):
        random_bytes = f"payload_{uuid.uuid4().hex}".encode('utf-8')
        stream_source = io.BytesIO(random_bytes)

        auto_trigger = MagicMock()
        trigger_res = f"trig_{uuid.uuid4().hex[:6]}"
        auto_trigger.trigger.return_value = trigger_res
        self.controller.market_portfolio_stress_auto_rebalance_trigger = auto_trigger

        with patch('requests.post') as mock_post:
            res = self.controller.execute_auto_hedge(self.event_id, stream_source)
            mock_post.assert_called_once_with("http://localhost/api/hedge", data=random_bytes)
            auto_trigger.trigger.assert_called_once_with(self.event_id, random_bytes)
            self.assertEqual(res, trigger_res)

    def test_execute_auto_hedge_no_trigger(self):
        random_bytes = f"payload_{uuid.uuid4().hex}".encode('utf-8')
        stream_source = io.BytesIO(random_bytes)

        if hasattr(self.controller, "market_portfolio_stress_auto_rebalance_trigger"):
            delattr(self.controller, "market_portfolio_stress_auto_rebalance_trigger")

        with patch('requests.post') as mock_post:
            res = self.controller.execute_auto_hedge(self.event_id, stream_source)
            mock_post.assert_called_once_with("http://localhost/api/hedge", data=random_bytes)
            self.assertTrue(res)

    def test_process_market_stream_default(self):
        content = f"stream_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(content)
        res = self.controller.process_market_stream(stream)
        self.assertEqual(res, content)

    def test_process_market_stream_with_parser(self):
        content = f"stream_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(content)
        parser = MagicMock()
        parsed_output = f"parsed_{uuid.uuid4().hex}"
        parser.parse_stream.return_value = parsed_output
        self.controller.market_parser = parser

        res = self.controller.process_market_stream(stream)
        parser.parse_stream.assert_called_once_with(stream)
        self.assertEqual(res, parsed_output)

    def test_notify_stakeholders_default(self):
        msg = f"msg_{uuid.uuid4().hex}"
        res = self.controller.notify_stakeholders(msg)
        self.assertEqual(res, {"status": "sent", "id": msg})

    def test_notify_stakeholders_with_notifier(self):
        msg = f"msg_{uuid.uuid4().hex}"
        notifier = MagicMock()
        notif_res = f"notif_{uuid.uuid4().hex}"
        notifier.send_message.return_value = notif_res
        self.controller.market_portfolio_telegram_notifier = notifier

        res = self.controller.notify_stakeholders(msg)
        notifier.send_message.assert_called_once_with(msg)
        self.assertEqual(res, notif_res)

    def test_persist_audit_log_default(self):
        key = f"key_{uuid.uuid4().hex[:6]}"
        val = f"val_{uuid.uuid4().hex[:6]}"
        db = MagicMock()
        db.save.return_value = f"saved_{uuid.uuid4().hex[:4]}"
        self.controller.db_storage = db

        res = self.controller.persist_audit_log(key, val)
        db.save.assert_called_once_with(key, val)
        self.assertEqual(res, db.save.return_value)

    def test_run_monte_carlo_stress_test_default(self):
        runs = random.randint(10, 100)
        res = self.controller.run_monte_carlo_stress_test(runs)
        self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_with_engine(self):
        runs = random.randint(10, 100)
        engine = MagicMock()
        engine_res = {"runs": runs, "outcome": uuid.uuid4().hex}
        engine.run.return_value = engine_res
        self.controller.market_portfolio_stress_monte_carlo_engine = engine

        res = self.controller.run_monte_carlo_stress_test(runs)
        engine.run.assert_called_once_with(runs)
        self.assertEqual(res, engine_res)

    def test_evaluate_and_execute_hedge(self):
        self.controller.execution_pipeline = MagicMock()
        hedge_id = f"ord_{uuid.uuid4().hex[:8]}"
        self.controller.execution_pipeline.execute.return_value = hedge_id
        self.controller.db_storage = MagicMock()

        res = self.controller.evaluate_and_execute_hedge(self.portfolio_id, self.threshold)
        self.controller.execution_pipeline.execute.assert_called_once_with(self.portfolio_id, self.threshold)
        self.controller.db_storage.save_portfolio_hedge_state.assert_called_once_with(
            self.portfolio_id, {"last_executed_hedge_id": hedge_id}
        )
        self.assertEqual(res, {"hedge_order_id": hedge_id})

    def test_export_last_audit_report(self):
        report_path = self.controller.export_last_audit_report(self.portfolio_id)
        self.assertTrue(report_path.endswith(f"{self.portfolio_id}.txt"))
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(self.portfolio_id, content)

if __name__ == '__main__':
    unittest.main()