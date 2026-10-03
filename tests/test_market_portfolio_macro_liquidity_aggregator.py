import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os
from skills.market_portfolio_macro_liquidity_aggregator import (
    MarketPortfolioMacroLiquidityAggregator,
    market_portfolio_macro_liquidity_aggregator
)

class TestMarketPortfolioMacroLiquidityAggregator(unittest.TestCase):

    def test_aggregate_macro_liquidity_with_extractor_and_agent(self):
        token = uuid.uuid4().hex
        mock_extractor_1 = MagicMock()
        mock_collector_agent = MagicMock()
        expected_result = {"status": "ok", "liquidity": random.uniform(100.0, 1000.0)}
        mock_collector_agent.collect.return_value = expected_result

        aggregator = MarketPortfolioMacroLiquidityAggregator(
            extractor_tool_1790087207=mock_extractor_1,
            market_portfolio_collector_agent=mock_collector_agent
        )

        result = aggregator.aggregate_macro_liquidity(token)

        mock_extractor_1.extract.assert_called_once()
        mock_collector_agent.collect.assert_called_once_with(token)
        self.assertEqual(result, expected_result)

    def test_aggregate_macro_liquidity_without_agent(self):
        token = uuid.uuid4().hex
        mock_extractor_1 = MagicMock()

        aggregator = MarketPortfolioMacroLiquidityAggregator(
            extractor_tool_1790087207=mock_extractor_1
        )

        result = aggregator.aggregate_macro_liquidity(token)

        mock_extractor_1.extract.assert_called_once()
        self.assertIsNone(result)

    def test_compute_stress_index(self):
        random_bytes = os.urandom(random.randint(10, 100))
        url = f"http://{uuid.uuid4().hex}.local/stress"

        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(random_bytes)

        with patch('requests.get', return_value=mock_response) as mock_get:
            aggregator = MarketPortfolioMacroLiquidityAggregator()
            index_val = aggregator.compute_stress_index(url)

            mock_get.assert_called_once_with(url, stream=True, timeout=10)
            self.assertEqual(index_val, float(len(random_bytes)))

    def test_run_anomaly_pipeline_with_detector(self):
        anomaly_id = uuid.uuid4().hex
        mock_detector = MagicMock()
        expected_data = {"anomaly_id": anomaly_id, "severity": random.choice(["high", "medium", "low"])}
        mock_detector.analyze.return_value = expected_data

        aggregator = MarketPortfolioMacroLiquidityAggregator(
            market_anomaly_detector=mock_detector
        )

        result = aggregator.run_anomaly_pipeline(anomaly_id)

        mock_detector.analyze.assert_called_once_with(anomaly_id)
        self.assertEqual(result, expected_data)

    def test_run_anomaly_pipeline_without_detector(self):
        anomaly_id = uuid.uuid4().hex
        aggregator = MarketPortfolioMacroLiquidityAggregator()

        result = aggregator.run_anomaly_pipeline(anomaly_id)
        self.assertEqual(result, {})

    def test_export_audit_logs_with_exporter(self):
        export_path = f"/tmp/{uuid.uuid4().hex}.log"
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = export_path

        aggregator = MarketPortfolioMacroLiquidityAggregator(
            market_portfolio_audit_log_exporter=mock_exporter
        )

        result = aggregator.export_audit_logs(export_path)

        mock_exporter.export.assert_called_once_with(export_path)
        self.assertEqual(result, export_path)

    def test_export_audit_logs_without_exporter(self):
        export_path = f"/tmp/{uuid.uuid4().hex}.log"
        aggregator = MarketPortfolioMacroLiquidityAggregator()

        result = aggregator.export_audit_logs(export_path)
        self.assertEqual(result, "")

    def test_functional_market_portfolio_macro_liquidity_aggregator(self):
        portfolio_id = uuid.uuid4().hex
        macro_liquidity_index = random.uniform(0.1, 99.9)
        stress_factor = random.uniform(1.0, 10.0)
        audit_output_path = f"/tmp/{uuid.uuid4().hex}.txt"

        payload = {
            "portfolio_id": portfolio_id,
            "macro_liquidity_index": macro_liquidity_index,
            "stress_factor": stress_factor,
            "audit_output_path": audit_output_path
        }

        mock_db_storage = MagicMock()

        with patch('skills.market_portfolio_macro_liquidity_aggregator.db_storage', mock_db_storage):
            response = market_portfolio_macro_liquidity_aggregator(payload)

            self.assertEqual(response["status"], "success")
            self.assertEqual(response["aggregated_id"], f"agg_{portfolio_id}")

            mock_db_storage.assert_called_once_with({
                "action": "set",
                "portfolio_id": portfolio_id,
                "macro_liquidity_index": macro_liquidity_index,
                "stress_factor": stress_factor,
                "aggregated_id": f"agg_{portfolio_id}"
            })

            self.assertTrue(os.path.exists(audit_output_path))
            with open(audit_output_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(portfolio_id, content)
                self.assertIn(str(macro_liquidity_index), content)
                self.assertIn(str(stress_factor), content)
                self.assertIn(f"agg_{portfolio_id}", content)

            if os.path.exists(audit_output_path):
                os.remove(audit_output_path)

if __name__ == '__main__':
    unittest.main()