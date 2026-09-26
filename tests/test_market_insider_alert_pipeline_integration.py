import unittest
import os
import uuid
import tempfile
from skills.market_insider_alert_pipeline import MarketInsiderAlertPipelineModuleAPI


class TestMarketInsiderAlertPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.api = MarketInsiderAlertPipelineModuleAPI()
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)

        self.storage_fd, self.storage_file = tempfile.mkstemp(suffix=".json")
        os.close(self.storage_fd)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_pipeline_execution_real_flow(self):
        random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        random_signature = f"sig_{uuid.uuid4().hex}"
        random_stream = f"insider volume anomaly spike {uuid.uuid4().hex}"

        payload = {
            "ticker": random_ticker,
            "raw_data_stream": random_stream,
            "signature": random_signature,
            "db_path": self.db_path,
            "storage_file": self.storage_file,
            "severity_level": "HIGH",
            "min_threshold": 50.0,
            "channels": ["telegram"],
            "url": "http://127.0.0.1:9999/webhook",
            "telegram_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u1234",
            "chat_id": "-100123456789"
        }

        result = self.api.execute_pipeline(payload)

        self.assertIn("status", result)
        self.assertIn("signature", result)
        self.assertIn("ticker", result)
        self.assertIn("alert_sent", result)

        self.assertEqual(result["ticker"], random_ticker)
        self.assertIsInstance(result["status"], str)
        self.assertIsInstance(result["alert_sent"], bool)

        if result["status"] == "anomaly":
            self.assertTrue(result["alert_sent"])
        else:
            self.assertFalse(result["alert_sent"])

        self.assertTrue(os.path.exists(self.db_path))


if __name__ == "__main__":
    unittest.main()