import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_insider_anomaly_report_bridge import (
    MarketInsiderAnomalyReportBridge,
    generate_insider_anomaly_report_investigation
)
from skills.market_insider_anomaly_analyzer import MarketInsiderAnomalyAnalyzer
from skills.market_report_generator import MarketReportGenerator


class TestMarketInsiderAnomalyReportBridge(unittest.TestCase):

    def setUp(self):
        self.random_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_exchange = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.random_storage = f"/tmp/{uuid.uuid4().hex}.db"
        self.random_stream_data = {uuid.uuid4().hex: random.random() for _ in range(3)}
        self.random_report_url = f"https://{uuid.uuid4().hex}.market/api/report"

    def test_bridge_composition_and_analysis_flow(self):
        mock_analyzer = MagicMock(spec=MarketInsiderAnomalyAnalyzer)
        expected_anomaly_result = {uuid.uuid4().hex: uuid.uuid4().hex, "score": random.uniform(1.0, 100.0)}
        mock_analyzer.analyze.return_value = expected_anomaly_result

        mock_generator = MagicMock(spec=MarketReportGenerator)
        expected_report_data = {uuid.uuid4().hex: uuid.uuid4().hex, "status": "generated"}
        mock_generator.generate_symbol_report.return_value = expected_report_data

        bridge = MarketInsiderAnomalyReportBridge(
            analyzer=mock_analyzer,
            report_generator=mock_generator
        )

        investigation_result = bridge.build_investigation(
            ticker=self.random_ticker,
            exchange=self.random_exchange,
            stream_data=self.random_stream_data
        )

        mock_analyzer.analyze.assert_called_once_with(self.random_ticker, self.random_stream_data)
        mock_generator.generate_symbol_report.assert_called_once_with(self.random_ticker)

        self.assertIn("anomaly_analysis", investigation_result)
        self.assertIn("market_report", investigation_result)
        self.assertEqual(investigation_result["anomaly_analysis"], expected_anomaly_result)
        self.assertEqual(investigation_result["market_report"], expected_report_data)

    def test_functional_bridge_wrapper_execution(self):
        sub_key = uuid.uuid4().hex
        sub_val = uuid.uuid4().hex
        report_url = f"http://{uuid.uuid4().hex}.local/dump"

        with patch('skills.market_insider_anomaly_report_bridge.MarketInsiderAnomalyAnalyzer') as MockAnalyzerClass, \
             patch('skills.market_insider_anomaly_report_bridge.MarketReportGenerator') as MockGeneratorClass:
            
            instance_analyzer = MockAnalyzerClass.return_value
            instance_analyzer.analyze.return_value = {sub_key: sub_val}

            instance_generator = MockGeneratorClass.return_value
            instance_generator.update_and_fetch_report.return_value = {uuid.uuid4().hex: self.random_ticker}

            result = generate_insider_anomaly_report_investigation(
                ticker=self.random_ticker,
                exchange=self.random_exchange,
                raw_stream_data=self.random_stream_data,
                storage_file=self.random_storage,
                report_url=report_url
            )

            instance_analyzer.analyze.assert_called_once_with(self.random_ticker, self.random_stream_data)
            instance_generator.update_and_fetch_report.assert_called_once_with(report_url, self.random_ticker)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["anomaly"][sub_key], sub_val)
            self.assertEqual(result["ticker"], self.random_ticker)

    def test_bridge_with_io_stream_dump_integration(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)

        mock_analyzer = MagicMock(spec=MarketInsiderAnomalyAnalyzer)
        mock_analyzer.correlate.return_value = {uuid.uuid4().hex: True}

        mock_generator = MagicMock(spec=MarketReportGenerator)
        mock_generator.get_raw_stream_dump.return_value = mock_stream

        bridge = MarketInsiderAnomalyReportBridge(
            analyzer=mock_analyzer,
            report_generator=mock_generator
        )

        dump_analysis = bridge.investigate_raw_stream_dump(
            ticker=self.random_ticker,
            stream_data=self.random_stream_data
        )

        mock_generator.get_raw_stream_dump.assert_called_once()
        self.assertEqual(dump_analysis["raw_bytes_len"], len(random_bytes))
        self.assertIn("correlation", dump_analysis)


if __name__ == '__main__':
    unittest.main()