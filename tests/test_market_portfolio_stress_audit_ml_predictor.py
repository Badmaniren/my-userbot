import unittest
from unittest.mock import patch
import random
import uuid
import io

from skills.market_portfolio_stress_audit_ml_predictor import start_new


class TestMarketPortfolioStressAuditMlPredictor(unittest.TestCase):

    def test_start_new_db_failure(self):
        rand_key = uuid.uuid4().hex
        rand_err = f"err_{uuid.uuid4().hex}"

        mock_db = unittest.mock.MagicMock()
        mock_db.query.return_value = {"status": "failed", "error": rand_err}

        with patch('skills.market_portfolio_stress_audit_ml_predictor.db_storage', mock_db):
            res = start_new({"portfolio_id": rand_key})
            self.assertEqual(res.get("status"), "failed")
            self.assertEqual(res.get("error"), rand_err)

    def test_start_new_stream_target(self):
        rand_stream = f"stream_{uuid.uuid4().hex}"
        rand_path = f"/var/log/{uuid.uuid4().hex}.log"
        rand_bytes = bytes(uuid.uuid4().hex, 'utf-8')

        mock_collector = unittest.mock.MagicMock()
        mock_collector.fetch_stream.return_value = io.BytesIO(rand_bytes)

        mock_exporter = unittest.mock.MagicMock()
        mock_exporter.export.return_value = rand_path

        with patch('skills.market_portfolio_stress_audit_ml_predictor.market_portfolio_collector_agent', mock_collector), \
             patch('skills.market_portfolio_stress_audit_ml_predictor.market_portfolio_stress_audit_exporter_v2', mock_exporter):

            res = start_new({"stream_target": rand_stream})
            self.assertEqual(res.get("export_path"), rand_path)
            mock_collector.fetch_stream.assert_called_once_with(rand_stream)

    def test_start_new_anomaly_detected(self):
        rand_payload = {"portfolio_id": uuid.uuid4().hex}

        mock_detector = unittest.mock.MagicMock()
        mock_detector.detect.return_value = {"is_anomaly": True, "score": random.random()}

        mock_dispatcher = unittest.mock.MagicMock()

        with patch('skills.market_portfolio_stress_audit_ml_predictor.market_anomaly_detector', mock_detector), \
             patch('skills.market_portfolio_stress_audit_ml_predictor.market_portfolio_alert_dispatcher', mock_dispatcher):

            res = start_new(rand_payload)
            self.assertTrue(res.get("anomaly_handled"))
            mock_dispatcher.dispatch.assert_called_once()

    def test_start_new_predictive_aggregator(self):
        rand_payload = {"portfolio_id": uuid.uuid4().hex}
        rand_token = f"tok_{uuid.uuid4().hex}"
        rand_drawdown = random.uniform(-1.0, 0.0)

        mock_aggregator = unittest.mock.MagicMock()
        mock_aggregator.aggregate_predictions.return_value = {
            "token": rand_token,
            "predicted_drawdown": rand_drawdown
        }

        with patch('skills.market_portfolio_stress_audit_ml_predictor.market_anomaly_detector', None), \
             patch('skills.market_portfolio_stress_audit_ml_predictor.market_portfolio_predictive_aggregator', mock_aggregator):

            res = start_new(rand_payload)
            self.assertEqual(res.get("predicted_token"), rand_token)
            self.assertEqual(res.get("drawdown"), rand_drawdown)

    def test_start_new_main_flow(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_payload = {"portfolio_id": rand_portfolio_id}
        rand_eval = {"eval_key": uuid.uuid4().hex}
        rand_mc = {"mc_key": uuid.uuid4().hex}
        rand_db = {"db_key": uuid.uuid4().hex}

        mock_pipeline = unittest.mock.MagicMock()
        mock_pipeline.evaluate.return_value = rand_eval

        mock_mc = unittest.mock.MagicMock()
        mock_mc.run_simulation.return_value = rand_mc

        mock_db = unittest.mock.MagicMock()
        mock_db.query.return_value = rand_db

        with patch('skills.market_portfolio_stress_audit_ml_predictor.market_anomaly_detector', None), \
             patch('skills.market_portfolio_stress_audit_ml_predictor.market_portfolio_predictive_aggregator', None), \
             patch('skills.market_portfolio_stress_audit_ml_predictor.market_portfolio_stress_scenario_pipeline', mock_pipeline), \
             patch('skills.market_portfolio_stress_audit_ml_predictor.market_portfolio_stress_monte_carlo_engine', mock_mc), \
             patch('skills.market_portfolio_stress_audit_ml_predictor.db_storage', mock_db):

            res = start_new(rand_payload)
            self.assertEqual(res.get("portfolio_id"), rand_portfolio_id)
            metrics = res.get("audit_metrics", {})
            self.assertEqual(metrics.get("pipeline_evaluation"), rand_eval)
            self.assertEqual(metrics.get("monte_carlo"), rand_mc)
            self.assertEqual(metrics.get("db_key"), rand_db.get("db_key"))