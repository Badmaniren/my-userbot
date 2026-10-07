import unittest
from unittest.mock import patch, MagicMock
import io
import json
import random
import uuid
from skills.market_portfolio_stress_diagnostic_telemetry import (
    TelemetryValidationError,
    StressDiagnosticTelemetryCollector,
    market_portfolio_stress_diagnostic_telemetry_run,
    db_storage_save,
    db_storage_get
)

class TestMarketPortfolioStressDiagnosticTelemetry(unittest.TestCase):
    def setUp(self):
        self.db_url = f"sqlite:///{uuid.uuid4().hex}.db"
        self.collector = StressDiagnosticTelemetryCollector(db_storage_url=self.db_url)
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.session_id = f"sess_{uuid.uuid4().hex[:8]}"

    def test_collect_and_validate_success(self):
        rand_var = round(random.uniform(1.0, 99.0), 2)
        rand_score = round(random.uniform(10.0, 500.0), 2)
        rand_conf = round(random.uniform(0.5, 1.0), 2)
        rand_anomaly = random.choice([True, False])

        mock_mc_res = {"var_95": rand_var, "stress_score": rand_score}
        mock_anomaly_res = {"anomaly_detected": rand_anomaly, "confidence": rand_conf}

        with patch("skills.market_portfolio_stress_monte_carlo_engine.run_simulation", return_value=mock_mc_res) as p_mc, \
             patch("skills.market_anomaly_detector.detect_anomalies", return_value=mock_anomaly_res) as p_anom, \
             patch("skills.db_storage.commit") as p_commit:

            res = self.collector.collect_and_validate(self.portfolio_id, self.session_id)

            p_mc.assert_called_once_with(portfolio_id=self.portfolio_id, session_id=self.session_id)
            p_anom.assert_called_once_with(portfolio_id=self.portfolio_id, session_id=self.session_id)
            p_commit.assert_called_once()

            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["session_id"], self.session_id)
            self.assertEqual(res["var_95"], rand_var)
            self.assertEqual(res["stress_score"], rand_score)
            self.assertEqual(res["anomaly_detected"], rand_anomaly)
            self.assertEqual(res["confidence"], rand_conf)

    def test_validate_audit_stream_valid_json(self):
        stream_id = f"stream_{uuid.uuid4().hex[:8]}"
        payload = {str(uuid.uuid4()): random.randint(1, 100) for _ in range(3)}
        encoded_data = json.dumps(payload).encode('utf-8')
        mock_stream = io.BytesIO(encoded_data)

        with patch("skills.market_portfolio_audit_log_exporter.export_stream", return_value=mock_stream) as p_export:
            self.collector.validate_audit_stream(stream_id)
            p_export.assert_called_once_with(stream_id=stream_id)

    def test_validate_audit_stream_invalid_json(self):
        stream_id = f"stream_{uuid.uuid4().hex[:8]}"
        corrupted_data = f"BROKEN_DATA_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(corrupted_data)

        with patch("skills.market_portfolio_audit_log_exporter.export_stream", return_value=mock_stream):
            with self.assertRaises(TelemetryValidationError):
                self.collector.validate_audit_stream(stream_id)

    def test_parse_external_stress_feed(self):
        feed_url = f"https://risk-metrics-{uuid.uuid4().hex[:6]}.org/feed"
        rand_title = f"Stress Indicator {uuid.uuid4().hex[:4]}"
        rand_val = round(random.uniform(5.0, 95.5), 2)
        html_content = f"""
        <html>
            <body>
                <div class="stress-indicator">
                    <h1>{rand_title}</h1>
                    <span class="val">{rand_val}</span>
                </div>
            </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = html_content

        with patch("requests.get", return_value=mock_response) as p_get:
            parsed = self.collector.parse_external_stress_feed(feed_url)
            p_get.assert_called_once_with(feed_url, timeout=10)
            self.assertEqual(parsed["title"], rand_title)
            self.assertEqual(parsed["value"], float(rand_val))

    def test_run_sentinel_check(self):
        context_id = f"ctx_{uuid.uuid4().hex[:8]}"
        threat_payload = {"threat_level": random.choice(["LOW", "HIGH", "CRITICAL"]), "score": random.random()}
        dispatch_response = {"status": "DISPATCHED", "id": uuid.uuid4().hex}

        with patch("skills.market_portfolio_autonomous_sentinel.evaluate_threat", return_value=threat_payload) as p_eval, \
             patch("skills.market_portfolio_alert_dispatcher.dispatch_alert", return_value=dispatch_response) as p_disp:

            result = self.collector.run_sentinel_check(context_id)
            p_eval.assert_called_once_with(context_id)
            p_disp.assert_called_once_with(threat_payload)
            self.assertEqual(result, dispatch_response)

    def test_evaluate_liquidity_stress(self):
        matrix_id = f"matrix_{uuid.uuid4().hex[:8]}"
        eval_result = {"matrix_id": matrix_id, "liquidity_ratio": random.random()}

        with patch("skills.market_portfolio_stress_scenario_matrix_evaluator.evaluate_matrix", return_value=eval_result) as p_eval:
            res = self.collector.evaluate_liquidity_stress(matrix_id)
            p_eval.assert_called_once_with(matrix_id)
            self.assertEqual(res, eval_result)

    def test_compile_financial_friction_report(self):
        tax_val = round(random.uniform(100.0, 5000.0), 2)
        cost_val = round(random.uniform(10.0, 500.0), 2)

        with patch("skills.market_portfolio_tax_calculator.calculate", return_value={"tax_liability": tax_val}) as p_tax, \
             patch("skills.market_portfolio_execution_cost_optimizer.optimize", return_value={"optimal_cost": cost_val}) as p_opt:

            report = self.collector.compile_financial_friction_report(self.portfolio_id)
            p_tax.assert_called_once_with(self.portfolio_id)
            p_opt.assert_called_once_with(self.portfolio_id)

            self.assertEqual(report["portfolio_id"], self.portfolio_id)
            self.assertEqual(report["tax_liability"], tax_val)
            self.assertEqual(report["execution_cost"], cost_val)

    def test_market_portfolio_stress_diagnostic_telemetry_run(self):
        salt = uuid.uuid4().hex
        res = market_portfolio_stress_diagnostic_telemetry_run(self.portfolio_id, salt)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertTrue(res["integrity_status"])
        self.assertIn(salt[:8], res["telemetry_id"])

    def test_db_storage_save_and_get(self):
        record_id = f"rec_{uuid.uuid4().hex[:8]}"
        payload = {"data": uuid.uuid4().hex}

        with patch("skills.db_storage.save", return_value=True) as p_save, \
             patch("skills.db_storage.get", return_value=payload) as p_get:

            saved = db_storage_save(record_id, payload)
            p_save.assert_called_once_with(record_id, payload)
            self.assertTrue(saved)

            fetched = db_storage_get(record_id)
            p_get.assert_called_once_with(record_id)
            self.assertEqual(fetched, payload)