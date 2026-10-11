import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_audit_regulatory_feed import RegulatoryFeedAggregator


class TestMarketPortfolioAuditRegulatoryFeed(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool = MagicMock()
        self.market_parser = MagicMock()
        self.audit_compliance_hub = MagicMock()

        self.aggregator = RegulatoryFeedAggregator(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_parser=self.market_parser,
            audit_compliance_hub=self.audit_compliance_hub
        )

    def test_fetch_and_store_regulations_success(self):
        rand_prefix = "".join(random.choices(string.ascii_lowercase, k=8))
        rand_url = f"https://{rand_prefix}.regulatory-{uuid.uuid4().hex[:6]}.gov/api/v1/feed"
        rand_html_content = f"<html><body><div id='content'>{uuid.uuid4().hex}</div></body></html>".encode('utf-8')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = rand_html_content
        mock_response.text = rand_html_content.decode('utf-8')

        with patch('requests.get', return_value=mock_response) as mock_get, \
             patch('bs4.BeautifulSoup') as mock_bs:

            mock_soup_instance = MagicMock()
            mock_bs.return_value = mock_soup_instance
            rand_extracted_rule = f"RULE-{uuid.uuid4().hex.upper()}"
            mock_soup_instance.find.return_value.text = rand_extracted_rule

            result = self.aggregator.fetch_and_store_feed(rand_url)

            mock_get.assert_called_once_with(rand_url, timeout=10)
            self.assertTrue(result)
            self.db_storage.save_regulation.assert_called_once()
            args, kwargs = self.db_storage.save_regulation.call_args
            self.assertIn(rand_extracted_rule, str(args))

    def test_fetch_regulations_network_failure(self):
        rand_url = f"https://fail-{uuid.uuid4().hex[:8]}.org/feed"

        with patch('requests.get', side_effect=requests.exceptions.RequestException("Network Error")) as mock_get:
            result = self.aggregator.fetch_and_store_feed(rand_url)

            mock_get.assert_called_once_with(rand_url, timeout=10)
            self.assertFalse(result)
            self.db_storage.save_regulation.assert_not_called()

    def test_parse_regulatory_document_stream(self):
        rand_bytes = f"REGULATION_DATA_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(rand_bytes)

        rand_doc_id = str(uuid.uuid4())

        with patch('skills.market_portfolio_audit_regulatory_feed.extract_stream_data', return_value=rand_bytes.decode('utf-8')) as mock_extractor:
            parsed_data = self.aggregator.parse_document_stream(mock_stream, rand_doc_id)

            mock_extractor.assert_called_once()
            self.assertIsNotNone(parsed_data)
            self.assertIn(rand_doc_id, parsed_data.get('document_id', ''))

    def test_audit_compliance_broker_sync(self):
        rand_rule_code = f"RULE-{random.randint(1000, 9999)}-{uuid.uuid4().hex[:4]}"
        rand_portfolio_id = f"PORT-{uuid.uuid4().hex[:8]}"

        self.db_storage.get_active_regulations.return_value = [
            {"code": rand_rule_code, "severity": "HIGH", "threshold": random.uniform(0.01, 0.15)}
        ]

        audit_result = self.aggregator.run_compliance_audit(rand_portfolio_id)

        self.assertIn("status", audit_result)
        self.assertIn(rand_portfolio_id, audit_result.get("portfolio_id", ""))
        self.audit_compliance_hub.verify_rule.assert_called()

    def test_anomaly_regulatory_trigger(self):
        rand_anomaly_id = str(uuid.uuid4())
        rand_severity = random.choice(["CRITICAL", "WARNING", "INFO"])

        payload = {
            "anomaly_id": rand_anomaly_id,
            "severity": rand_severity,
            "metric": random.uniform(10.0, 500.0)
        }

        with patch.object(self.aggregator, 'dispatch_alert') as mock_dispatch:
            self.aggregator.handle_market_anomaly(payload)
            mock_dispatch.assert_called_once()
            called_args = mock_dispatch.call_args[0][0]
            self.assertEqual(called_args["anomaly_id"], rand_anomaly_id)


if __name__ == '__main__':
    unittest.main()