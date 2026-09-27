import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_insider_investigation_hub import (
    MarketInsiderInvestigationHub,
    conduct_insider_investigation
)


class TestMarketInsiderInvestigationHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.ticker = "".join(random.choices(string.ascii_uppercase, k=4))
        self.exchange = random.choice(["NASDAQ", "NYSE", "LSE", "MOEX"])
        self.stream_data = {
            "volume": random.randint(1000, 1000000),
            "price_delta": random.uniform(-5.0, 5.0),
            "entity": uuid.uuid4().hex
        }

    @patch("skills.market_insider_investigation_hub.MarketInsiderAnomalyReportBridge")
    @patch("skills.market_insider_investigation_hub.MarketParser")
    def test_investigation_hub_composition_and_storage(self, mock_market_parser_cls, mock_bridge_cls):
        mock_parser_instance = mock_market_parser_cls.return_value
        mock_bridge_instance = mock_bridge_cls.return_value

        expected_report = {
            "investigation_id": uuid.uuid4().hex,
            "status": "anomaly_detected",
            "risk_score": random.uniform(50.0, 99.9)
        }
        mock_bridge_instance.build_investigation.return_value = expected_report

        hub = MarketInsiderInvestigationHub(storage_file=self.storage_file)

        mock_market_parser_cls.assert_called_once_with(self.storage_file)

        result = hub.investigate_and_store(self.ticker, self.exchange, self.stream_data)

        mock_bridge_instance.build_investigation.assert_called_once_with(
            ticker=self.ticker,
            exchange=self.exchange,
            stream_data=self.stream_data
        )

        mock_parser_instance.fetch_and_store.assert_called_once()
        self.assertEqual(result, expected_report)

    @patch("skills.market_insider_investigation_hub.MarketInsiderAnomalyReportBridge")
    @patch("skills.market_insider_investigation_hub.MarketParser")
    def test_conduct_insider_investigation_functional_flow(self, mock_market_parser_cls, mock_bridge_cls):
        mock_bridge_instance = mock_bridge_cls.return_value
        random_url = f"https://{uuid.uuid4().hex}.market/api/stream"

        expected_dump_analysis = {
            "ticker": self.ticker,
            "anomaly_detected": True,
            "raw_stream_hash": uuid.uuid4().hex
        }
        mock_bridge_instance.investigate_raw_stream_dump.return_value = expected_dump_analysis

        result = conduct_insider_investigation(
            ticker=self.ticker,
            exchange=self.exchange,
            stream_data=self.stream_data,
            storage_file=self.storage_file,
            report_url=random_url
        )

        mock_bridge_instance.investigate_raw_stream_dump.assert_called_once_with(
            ticker=self.ticker,
            stream_data=self.stream_data
        )
        self.assertEqual(result, expected_dump_analysis)

    @patch("skills.market_insider_investigation_hub.MarketInsiderAnomalyReportBridge")
    @patch("skills.market_insider_investigation_hub.MarketParser")
    def test_investigation_hub_handles_empty_stream(self, mock_market_parser_cls, mock_bridge_cls):
        mock_bridge_instance = mock_bridge_cls.return_value
        empty_stream = {}

        mock_bridge_instance.build_investigation.return_value = {"error": "empty_stream"}

        hub = MarketInsiderInvestigationHub(storage_file=self.storage_file)
        result = hub.investigate_and_store(self.ticker, self.exchange, empty_stream)

        self.assertIn("error", result)
        self.assertEqual(result["error"], "empty_stream")


if __name__ == "__main__":
    unittest.main()