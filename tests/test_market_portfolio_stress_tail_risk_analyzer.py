import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys

from skills.market_portfolio_stress_tail_risk_analyzer import TailRiskAnalyzer

class TestTailRiskAnalyzer(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.monte_carlo_engine = MagicMock()
        self.stress_reporter = MagicMock()
        self.analyzer = TailRiskAnalyzer(
            db_storage=self.db_storage,
            monte_carlo_engine=self.monte_carlo_engine,
            stress_reporter=self.stress_reporter
        )

    def test_calculate_tail_risk_metrics_success(self):
        portfolio_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.95, 0.99), 4)
        simulated_returns = [random.uniform(-0.15, 0.05) for _ in range(100)]

        self.monte_carlo_engine.run_simulation.return_value = simulated_returns

        result = self.analyzer.calculate_tail_risk(portfolio_id, confidence_level)

        self.assertIn("var", result)
        self.assertIn("expected_shortfall", result)
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIsInstance(result["var"], float)
        self.assertIsInstance(result["expected_shortfall"], float)
        self.monte_carlo_engine.run_simulation.assert_called_once_with(portfolio_id)

    def test_evaluate_stress_tail_risk_with_io_stream(self):
        scenario_code = "".join(random.choices(string.ascii_uppercase, k=6))
        random_payload = f"risk_metric:{random.randint(100, 999)},loss:{random.uniform(10.0, 50.0)}".encode('utf-8')
        mock_io_stream = io.BytesIO(random_payload)

        with patch('skills.market_portfolio_stress_tail_risk_analyzer.open', return_value=mock_io_stream, create=True) as mock_file:
            assessment = self.analyzer.evaluate_external_scenario_stream(scenario_code)

            self.assertIn("scenario", assessment)
            self.assertEqual(assessment["scenario"], scenario_code)
            self.assertTrue(assessment["stream_processed"])
            self.assertGreater(assessment["extracted_loss"], 0.0)

    def test_anomaly_driven_tail_risk_adjustment(self):
        anomaly_id = str(uuid.uuid4())
        base_var = round(random.uniform(1000.0, 5000.0), 2)
        multiplier = round(random.uniform(1.1, 2.5), 2)

        anomaly_data = {
            "id": anomaly_id,
            "severity_multiplier": multiplier,
            "raw_anomaly_score": random.randint(50, 100)
        }

        with patch('skills.market_portfolio_stress_tail_risk_analyzer.market_anomaly_detector') as mock_detector:
            mock_detector.fetch_anomaly_details.return_value = anomaly_data

            adjusted_var = self.analyzer.adjust_var_for_anomaly(base_var, anomaly_id)

            expected_val = base_var * multiplier
            self.assertEqual(adjusted_var, expected_val)
            mock_detector.fetch_anomaly_details.assert_called_once_with(anomaly_id)

    def test_stress_reporter_integration_failure_handling(self):
        faulty_portfolio_id = str(uuid.uuid4())
        self.stress_reporter.generate_report.side_effect = Exception("Database connection timeout during reporting")

        with self.assertRaises(RuntimeError) as context:
            self.analyzer.generate_and_dispatch_tail_risk_report(faulty_portfolio_id)

        self.assertIn("Database connection timeout", str(context.exception))
        self.stress_reporter.generate_report.assert_called_once_with(faulty_portfolio_id)

    def test_telegram_alert_dispatch_on_extreme_risk(self):
        portfolio_id = str(uuid.uuid4())
        extreme_var_threshold = round(random.uniform(50000.0, 100000.0), 2)

        with patch('skills.market_portfolio_stress_tail_risk_analyzer.market_portfolio_telegram_notifier') as mock_notifier:
            self.analyzer.check_and_notify_extreme_tail_risk(portfolio_id, extreme_var_threshold)

            mock_notifier.send_critical_alert.assert_called_once()
            args, _ = mock_notifier.send_critical_alert.call_args
            self.assertIn(portfolio_id, str(args))

if __name__ == '__main__':
    unittest.main()