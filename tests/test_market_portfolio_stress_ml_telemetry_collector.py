import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.market_portfolio_stress_ml_telemetry_collector import (
    start_new,
    market_portfolio_stress_ml_telemetry_collector
)


class TestMarketPortfolioStressMlTelemetryCollector(unittest.TestCase):

    def test_start_new_executes_dependencies_and_requests(self):
        portfolio_id = uuid.uuid4().hex
        
        mock_collector_agent = MagicMock()
        mock_anomaly_detector = MagicMock()
        
        dependencies = {
            "market_portfolio_collector_agent": mock_collector_agent,
            "market_anomaly_detector": mock_anomaly_detector
        }

        with patch("skills.market_portfolio_stress_ml_telemetry_collector.requests.get") as mock_get, \
             patch("skills.market_portfolio_stress_ml_telemetry_collector.requests.post") as mock_post:

            result = start_new(dependencies, portfolio_id)

            mock_collector_agent.collect.assert_called_once_with(portfolio_id)
            mock_anomaly_detector.detect.assert_called_once_with(portfolio_id)
            
            mock_get.assert_called_once_with("https://localhost/telemetry", timeout=1)
            mock_post.assert_called_once_with(
                "https://localhost/telemetry/anomaly",
                json={"portfolio_id": portfolio_id},
                timeout=1
            )

            self.assertEqual(result, {"status": "ok", "portfolio_id": portfolio_id})

    def test_start_new_missing_dependencies_handles_gracefully(self):
        portfolio_id = uuid.uuid4().hex
        dependencies = {}

        with patch("skills.market_portfolio_stress_ml_telemetry_collector.requests.get") as mock_get, \
             patch("skills.market_portfolio_stress_ml_telemetry_collector.requests.post") as mock_post:

            result = start_new(dependencies, portfolio_id)
            
            mock_get.assert_called_once()
            mock_post.assert_called_once()
            self.assertEqual(result.get("portfolio_id"), portfolio_id)

    def test_market_portfolio_stress_ml_telemetry_collector_stores_and_returns(self):
        telemetry_id = uuid.uuid4().hex
        portfolio_id = uuid.uuid4().hex
        scenario_id = uuid.uuid4().hex
        matrix_metrics = {uuid.uuid4().hex: random.random()}
        var_liquidity_metrics = {uuid.uuid4().hex: random.random()}
        ml_feature_weight = random.random()

        payload = {
            "telemetry_id": telemetry_id,
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "matrix_metrics": matrix_metrics,
            "var_liquidity_metrics": var_liquidity_metrics,
            "ml_feature_weight": ml_feature_weight
        }

        with patch("skills.market_portfolio_stress_ml_telemetry_collector.db_storage") as mock_db_storage:
            result = market_portfolio_stress_ml_telemetry_collector(payload)

            expected_record = {
                "telemetry_id": telemetry_id,
                "portfolio_id": portfolio_id,
                "scenario_id": scenario_id,
                "matrix_metrics": matrix_metrics,
                "var_liquidity_metrics": var_liquidity_metrics,
                "ml_feature_weight": ml_feature_weight
            }

            mock_db_storage.assert_called_once_with({
                "query_type": "save_telemetry",
                "telemetry_id": telemetry_id,
                "record": expected_record
            })

            self.assertEqual(result, expected_record)


if __name__ == "__main__":
    unittest.main()