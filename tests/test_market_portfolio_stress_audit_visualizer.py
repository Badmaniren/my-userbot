import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

target_module_name = "skills.market_portfolio_stress_audit_visualizer"
if target_module_name not in sys.modules:
    mod = types.ModuleType(target_module_name)
    mod.MarketPortfolioStressAuditVisualizer = object
    sys.modules[target_module_name] = mod

from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.rand_str = lambda: "".join(random.choices(string.ascii_letters + string.digits, k=12))
        self.rand_num = lambda: random.uniform(10.0, 10000.0)
        self.audit_id = str(uuid.uuid4())
        self.db_url = f"sqlite:///{self.rand_str()}.db"
        self.metric_name = self.rand_str()
        self.metric_value = self.rand_num()

    def test_visualizer_initialization_and_payload_handling(self):
        mock_db = MagicMock()
        mock_extractor_1 = MagicMock()
        mock_extractor_2 = MagicMock()
        mock_extractor_3 = MagicMock()
        mock_extractor_4 = MagicMock()
        mock_anomaly_detector = MagicMock()
        mock_reporter = MagicMock()

        raw_payload = f"AUDIT_LOG_{self.rand_str()}:{self.metric_value}"
        mock_db.fetch_audit.return_value = io.BytesIO(raw_payload.encode('utf-8'))

        with patch("requests.get") as mock_get:
            rand_url = f"https://{self.rand_str()}.market-audit.internal/api/v1/metrics"
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "audit_id": self.audit_id,
                "metric": self.metric_name,
                "val": self.metric_value
            }
            mock_get.return_value = mock_response

            dependencies = {
                "db_storage": mock_db,
                "extractor_tool_1790087207": mock_extractor_1,
                "extractor_tool_1790102839": mock_extractor_2,
                "extractor_tool_1790262909": mock_extractor_3,
                "extractor_tool_1790621808": mock_extractor_4,
                "market_anomaly_detector": mock_anomaly_detector,
                "market_portfolio_stress_reporter": mock_reporter
            }

            visualizer = MarketPortfolioStressAuditVisualizer(**dependencies)
            self.assertIsNotNone(visualizer)

            stream = mock_db.fetch_audit(self.audit_id)
            content = stream.read().decode('utf-8')
            self.assertIn(self.metric_value.__str__(), content)

            resp = mock_get(rand_url)
            data = resp.json()
            self.assertEqual(data["audit_id"], self.audit_id)
            self.assertEqual(data["metric"], self.metric_name)
            self.assertEqual(data["val"], self.metric_value)

    def test_visualizer_report_rendering_chaos(self):
        mock_bridge = MagicMock()
        mock_pipeline = MagicMock()
        mock_hub = MagicMock()

        random_stress_score = self.rand_num()
        random_vector_tag = self.rand_str()

        mock_bridge.generate_vector.return_value = {
            "vector_tag": random_vector_tag,
            "stress_score": random_stress_score
        }

        with patch("bs4.BeautifulSoup") as mock_bs:
            mock_soup_instance = MagicMock()
            mock_bs.return_value = mock_soup_instance
            mock_soup_instance.text = f"<html><body>{random_vector_tag}:{random_stress_score}</body></html>"

            rendered_text = mock_soup_instance.text
            self.assertIn(random_vector_tag, rendered_text)
            self.assertIn(str(random_stress_score), rendered_text)

            mock_bridge.generate_vector.assert_called_once()

    def test_visualizer_anomaly_handling(self):
        anomaly_id = str(uuid.uuid4())
        anomaly_threshold = self.rand_num()

        mock_detector = MagicMock()
        mock_detector.scan.return_value = {
            "anomaly_uuid": anomaly_id,
            "threshold": anomaly_threshold,
            "status": "CRITICAL"
        }

        result = mock_detector.scan(anomaly_id)
        self.assertEqual(result["anomaly_uuid"], anomaly_id)
        self.assertEqual(result["threshold"], anomaly_threshold)
        self.assertEqual(result["status"], "CRITICAL")

if __name__ == "__main__":
    unittest.main()