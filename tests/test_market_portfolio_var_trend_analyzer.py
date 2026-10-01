import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.market_portfolio_var_trend_analyzer import VaRTrendAnalyzer

class TestVaRTrendAnalyzer(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_scenario_sim = MagicMock()
        self.mock_stress_reporter = MagicMock()

        self.analyzer = VaRTrendAnalyzer(
            db_storage=self.mock_db,
            market_portfolio_scenario_simulator=self.mock_scenario_sim,
            market_portfolio_stress_reporter=self.mock_stress_reporter
        )

    def test_analyze_var_trend_success(self):
        portfolio_id = str(uuid.uuid4())
        timeframe_days = random.randint(30, 365)

        random_var_values = [random.uniform(0.01, 0.15) for _ in range(10)]
        random_dates = [f"2023-{(i%12)+1:02d}-{(i%28)+1:02d}" for i in range(10)]

        db_mock_return = [
            {"date": d, "var_value": v} for d, v in zip(random_dates, random_var_values)
        ]

        with patch.object(self.analyzer, '_fetch_historical_var', return_value=db_mock_return) as mock_fetch:
            result = self.analyzer.analyze_trend(portfolio_id, timeframe_days)

            mock_fetch.assert_called_once_with(portfolio_id, timeframe_days)
            self.assertIn("trend_direction", result)
            self.assertIn("volatility_of_var", result)
            self.assertEqual(result["data_points_analyzed"], len(db_mock_return))

    def test_stress_test_trend_evaluation(self):
        scenario_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        portfolio_uuid = str(uuid.uuid4())
        expected_impact = random.uniform(-0.5, -0.05)

        stream_data = json.dumps({"scenario": scenario_name, "impact": expected_impact}).encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        with patch.object(self.mock_scenario_sim, 'run_monte_carlo', return_value=mock_stream) as mock_mc:
            analysis_result = self.analyzer.evaluate_stress_trend(portfolio_uuid, scenario_name)

            mock_mc.assert_called_once()
            self.assertEqual(analysis_result["scenario_evaluated"], scenario_name)
            self.assertAlmostEqual(analysis_result["simulated_impact"], expected_impact)

    def test_empty_historical_data_handling(self):
        random_pid = str(uuid.uuid4())
        random_days = random.randint(10, 90)

        with patch.object(self.analyzer, '_fetch_historical_var', return_value=[]) as mock_fetch:
            result = self.analyzer.analyze_trend(random_pid, random_days)

            mock_fetch.assert_called_once_with(random_pid, random_days)
            self.assertEqual(result["status"], "insufficient_data")
            self.assertEqual(result["data_points_analyzed"], 0)

    def test_export_trend_report_data(self):
        report_id = str(uuid.uuid4())
        risk_metric = ''.join(random.choices(string.ascii_uppercase, k=6))
        threshold = random.uniform(0.05, 0.25)

        mock_audit_logger = MagicMock()

        with patch('skills.market_portfolio_var_trend_analyzer.market_portfolio_audit_log_exporter', mock_audit_logger):
            export_payload = self.analyzer.generate_trend_audit_payload(report_id, risk_metric, threshold)

            self.assertEqual(export_payload["report_uuid"], report_id)
            self.assertEqual(export_payload["metric_monitored"], risk_metric)
            self.assertEqual(export_payload["alert_threshold"], threshold)
            self.assertTrue(export_payload["export_timestamp"])

if __name__ == '__main__':
    unittest.main()