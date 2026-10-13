import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
from skills.market_portfolio_stress_deep_forecaster import start_new

class TestMarketPortfolioStressDeepForecaster(unittest.TestCase):

    def setUp(self):
        self.random_string = uuid.uuid4().hex
        self.random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.random_scenario_name = f"scenario_{uuid.uuid4().hex[:6]}"
        self.random_confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.random_metric_value = random.randint(1000, 1000000)

    def test_start_new_execution_flow(self):
        mock_db = MagicMock()
        mock_db.fetch_historical_data.return_value = [
            {"timestamp": uuid.uuid4().hex, "value": random.uniform(10.0, 500.0)} for _ in range(5)
        ]
        
        mock_scenario_simulator = MagicMock()
        mock_scenario_simulator.run_matrix.return_value = {
            "scenario": self.random_scenario_name,
            "stress_index": random.uniform(1.0, 10.0),
            "loss_expectation": self.random_metric_value
        }

        with patch("skills.market_portfolio_stress_deep_forecaster.db_storage", mock_db), \
             patch("skills.market_portfolio_stress_deep_forecaster.market_portfolio_scenario_simulator", mock_scenario_simulator):
            
            result = start_new(portfolio_id=self.random_portfolio_id, confidence=self.random_confidence_level)
            
            self.assertIsInstance(result, dict)
            self.assertIn("status", result)
            self.assertEqual(result["portfolio_id"], self.random_portfolio_id)
            mock_db.fetch_historical_data.assert_called_once()
            mock_scenario_simulator.run_matrix.assert_called_once()

    def test_start_new_anomaly_detection_integration(self):
        random_anomaly_score = random.uniform(50.0, 100.0)
        mock_anomaly_detector = MagicMock()
        mock_anomaly_detector.evaluate_anomalies.return_value = {
            "anomaly_detected": True,
            "severity_score": random_anomaly_score,
            "signature": self.random_string
        }

        with patch("skills.market_portfolio_stress_deep_forecaster.market_anomaly_detector", mock_anomaly_detector):
            result = start_new(portfolio_id=self.random_portfolio_id, confidence=self.random_confidence_level)
            
            self.assertIn("anomaly_analysis", result)
            self.assertEqual(result["anomaly_analysis"]["severity_score"], random_anomaly_score)
            self.assertEqual(result["anomaly_analysis"]["signature"], self.random_string)
            mock_anomaly_detector.evaluate_anomalies.assert_called_once()

    def test_start_new_ml_stress_evaluation(self):
        random_ml_prediction = random.uniform(-0.5, -0.01)
        mock_ml_evaluator = MagicMock()
        mock_ml_evaluator.predict_stress.return_value = random_ml_prediction

        with patch("skills.market_portfolio_stress_deep_forecaster.market_portfolio_ml_stress_evaluator", mock_ml_evaluator):
            result = start_new(portfolio_id=self.random_portfolio_id, confidence=self.random_confidence_level)
            
            self.assertIn("ml_stress_prediction", result)
            self.assertEqual(result["ml_stress_prediction"], random_ml_prediction)
            mock_ml_evaluator.predict_stress.assert_called_once()

    def test_start_new_data_export_and_audit(self):
        random_audit_id = f"audit_{uuid.uuid4().hex}"
        mock_audit_exporter = MagicMock()
        mock_audit_exporter.export_audit_log.return_value = random_audit_id

        with patch("skills.market_portfolio_stress_deep_forecaster.market_portfolio_stress_audit_exporter_v2", mock_audit_exporter):
            result = start_new(portfolio_id=self.random_portfolio_id, confidence=self.random_confidence_level)
            
            self.assertIn("audit_id", result)
            self.assertEqual(result["audit_id"], random_audit_id)
            mock_audit_exporter.export_audit_log.assert_called_once()

    def test_start_new_exception_handling_and_recovery(self):
        mock_db = MagicMock()
        mock_db.fetch_historical_data.side_effect = Exception(self.random_string)

        with patch("skills.market_portfolio_stress_deep_forecaster.db_storage", mock_db):
            result = start_new(portfolio_id=self.random_portfolio_id, confidence=self.random_confidence_level)
            
            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
            self.assertIn(self.random_string, result["error"])

if __name__ == "__main__":
    unittest.main()