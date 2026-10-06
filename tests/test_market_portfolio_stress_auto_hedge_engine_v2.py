import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_stress_auto_hedge_engine_v2 import (
    StressAutoHedgeEngineV2,
    HedgeExecutionError,
    ScenarioEvaluationError
)

class TestStressAutoHedgeEngineV2(unittest.TestCase):

    def setUp(self):
        self.engine_id = str(uuid.uuid4())
        self.db_storage = MagicMock()
        self.scenario_simulator = MagicMock()
        self.execution_pipeline = MagicMock()
        self.risk_hub = MagicMock()

        self.engine = StressAutoHedgeEngineV2(
            engine_id=self.engine_id,
            db_storage=self.db_storage,
            market_portfolio_scenario_simulator=self.scenario_simulator,
            market_portfolio_execution_pipeline=self.execution_pipeline,
            market_sentiment_risk_hub=self.risk_hub
        )

    def test_evaluate_and_hedge_success(self):
        portfolio_id = str(uuid.uuid4())
        scenario_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        severity_score = random.uniform(50.0, 100.0)
        expected_hedge_asset = ''.join(random.choices(string.ascii_uppercase, k=5))
        allocated_volume = random.randint(100, 5000)

        self.scenario_simulator.evaluate.return_value = {
            "scenario": scenario_name,
            "severity": severity_score,
            "recommended_hedge": expected_hedge_asset,
            "volume": allocated_volume
        }

        exec_token = str(uuid.uuid4())
        self.execution_pipeline.execute_hedge.return_value = {
            "status": "EXECUTED",
            "token": exec_token
        }

        with patch('skills.market_portfolio_stress_auto_hedge_engine_v2.datetime') as mock_dt:
            random_timestamp = str(random.randint(1000000000, 2000000000))
            mock_dt.now.return_value.isoformat.return_value = random_timestamp

            result = self.engine.evaluate_and_hedge(portfolio_id, scenario_name)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["hedge_asset"], expected_hedge_asset)
        self.assertEqual(result["volume"], allocated_volume)
        self.assertEqual(result["execution_token"], exec_token)
        self.db_storage.save_hedge_log.assert_called_once()

    def test_evaluate_and_hedge_scenario_failure(self):
        portfolio_id = str(uuid.uuid4())
        scenario_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        error_message = ''.join(random.choices(string.ascii_letters + string.digits, k=15))

        self.scenario_simulator.evaluate.side_effect = Exception(error_message)

        with self.assertRaises(ScenarioEvaluationError) as ctx:
            self.engine.evaluate_and_hedge(portfolio_id, scenario_name)

        self.assertIn(error_message, str(ctx.exception))
        self.db_storage.save_error_log.assert_called_once()

    def test_execution_failure_handling(self):
        portfolio_id = str(uuid.uuid4())
        scenario_name = ''.join(random.choices(string.ascii_lowercase, k=6))

        self.scenario_simulator.evaluate.return_value = {
            "scenario": scenario_name,
            "severity": 85.5,
            "recommended_hedge": "GOLD",
            "volume": 500
        }

        exec_error_msg = ''.join(random.choices(string.ascii_letters, k=12))
        self.execution_pipeline.execute_hedge.side_effect = requests.RequestException(exec_error_msg)

        with self.assertRaises(HedgeExecutionError) as ctx:
            self.engine.evaluate_and_hedge(portfolio_id, scenario_name)

        self.assertIn(exec_error_msg, str(ctx.exception))
        self.risk_hub.report_critical_failure.assert_called_once()

    def test_parse_market_sentiment_feed(self):
        random_html_id = str(uuid.uuid4())
        random_text_content = ''.join(random.choices(string.ascii_letters, k=20))
        raw_html = f"<html><body><div id='{random_html_id}'>{random_text_content}</div></body></html>"

        byte_stream = io.BytesIO(raw_html.encode('utf-8'))

        with patch('skills.market_portfolio_stress_auto_hedge_engine_v2.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = byte_stream.read()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            target_url = f"https://{uuid.uuid4().hex}.com/feed"
            parsed_data = self.engine.parse_sentiment_feed(target_url, random_html_id)

        self.assertEqual(parsed_data, random_text_content)

    def test_anomaly_triggers_auto_hedge(self):
        anomaly_id = str(uuid.uuid4())
        portfolio_id = str(uuid.uuid4())
        anomaly_payload = {
            "anomaly_id": anomaly_id,
            "portfolio_id": portfolio_id,
            "deviation_score": random.uniform(10.0, 99.9)
        }

        self.execution_pipeline.emergency_hedge.return_value = {
            "status": "FORCED_HEDGE",
            "anomaly_id": anomaly_id
        }

        res = self.engine.handle_anomaly_trigger(anomaly_payload)

        self.assertEqual(res["anomaly_id"], anomaly_id)
        self.assertEqual(res["status"], "FORCED_HEDGE")
        self.execution_pipeline.emergency_hedge.assert_called_once_with(anomaly_payload)

if __name__ == '__main__':
    unittest.main()