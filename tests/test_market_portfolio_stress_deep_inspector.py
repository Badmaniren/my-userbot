import unittest
from unittest.mock import MagicMock, patch
import json
import uuid
import random
import io
import os

from skills.market_portfolio_stress_deep_inspector import (
    DeepStressInspectorEngine,
    inspect_portfolio_deep_stress_vulnerabilities,
    inspect_portfolio_stress_vulnerabilities
)


class TestMarketPortfolioStressDeepInspector(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.severity_threshold = random.randint(1, 100)
        self.audit_token = uuid.uuid4().hex
        self.scenario_id = uuid.uuid4().hex
        self.report_target = uuid.uuid4().hex

    def test_deep_stress_inspector_engine_analyze_deep_risk(self):
        mock_db = MagicMock()
        mock_var = MagicMock()
        mock_audit = MagicMock()

        engine = DeepStressInspectorEngine(
            db_storage=mock_db,
            market_portfolio_var_liquidity_core=mock_var,
            market_portfolio_audit_compliance_hub=mock_audit
        )

        result = engine.analyze_deep_risk(self.portfolio_id, self.severity_threshold)

        mock_db.fetch_raw_logs.assert_called_once_with(self.portfolio_id)
        mock_var.evaluate_liquidity_risk.assert_called_once_with(self.portfolio_id, self.severity_threshold)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["severity_threshold"], self.severity_threshold)
        self.assertEqual(result["status"], "analyzed")

    def test_deep_stress_inspector_engine_audit_deep_stress_state(self):
        mock_db = MagicMock()
        mock_stream = MagicMock()
        mock_db.get_audit_stream.return_value = mock_stream

        mock_audit = MagicMock()
        expected_key = uuid.uuid4().hex
        mock_audit.verify_compliance.return_value = {"compliant": True, "key": expected_key}

        engine = DeepStressInspectorEngine(
            db_storage=mock_db,
            market_portfolio_audit_compliance_hub=mock_audit
        )

        result = engine.audit_deep_stress_state(self.portfolio_id, self.audit_token)

        mock_db.get_audit_stream.assert_called_once_with(self.portfolio_id)
        mock_audit.verify_compliance.assert_called_once_with(self.portfolio_id, self.audit_token)

        self.assertTrue(result["compliant"])
        self.assertEqual(result["audit_key"], expected_key)
        self.assertEqual(result["target_portfolio"], self.portfolio_id)
        self.assertTrue(result["stream_available"])

    def test_inspect_portfolio_deep_stress_vulnerabilities(self):
        mock_db = MagicMock()
        token_val = uuid.uuid4().hex
        report_payload = json.dumps({"token": token_val})
        mock_stream = io.BytesIO(report_payload.encode('utf-8'))
        mock_db.fetch_stress_report.return_value = mock_stream

        mock_simulator = MagicMock()
        vulnerability_score = random.uniform(0.1, 0.9)
        mock_simulator.run_simulation.return_value = {"vulnerability_index": vulnerability_score}

        with patch("skills.market_portfolio_stress_deep_inspector.market_portfolio_valuation", create=True) as mock_valuation:
            result = inspect_portfolio_deep_stress_vulnerabilities(
                db_storage=mock_db,
                market_portfolio_scenario_simulator=mock_simulator,
                market_portfolio_var_liquidity_core=MagicMock(),
                market_portfolio_audit_compliance_hub=MagicMock(),
                portfolio_id=self.portfolio_id,
                report_target=self.report_target
            )

            mock_db.fetch_stress_report.assert_called_once_with(self.report_target)
            mock_simulator.run_simulation.assert_called_once_with(portfolio_id=self.portfolio_id)
            mock_valuation.calculate_portfolio_value.assert_called_once_with(self.portfolio_id)

            self.assertTrue(result["vulnerabilities_detected"])
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["scenario_token"], token_val)
            self.assertEqual(result["risk_score"], vulnerability_score)

    def test_inspect_portfolio_stress_vulnerabilities_integration(self):
        scenario_data = {"scenario_id": self.scenario_id}
        monte_carlo_metrics = {"var_95": random.uniform(100.0, 500.0), "cvar_95": random.uniform(200.0, 800.0)}

        report_payload = inspect_portfolio_stress_vulnerabilities(
            portfolio_id=self.portfolio_id,
            scenario_data=scenario_data,
            monte_carlo_metrics=monte_carlo_metrics
        )

        self.assertEqual(report_payload["portfolio_id"], self.portfolio_id)
        self.assertEqual(report_payload["scenario_id"], self.scenario_id)
        self.assertEqual(report_payload["mc_metrics"], monte_carlo_metrics)
        self.assertIn("inspection_id", report_payload)
        self.assertIn("report_file_path", report_payload)

        report_file = report_payload["report_file_path"]
        self.assertTrue(os.path.exists(report_file))

        try:
            with open(report_file, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
            self.assertEqual(loaded_data["portfolio_id"], self.portfolio_id)
            self.assertEqual(loaded_data["scenario_id"], self.scenario_id)
        finally:
            if os.path.exists(report_file):
                os.remove(report_file)


if __name__ == "__main__":
    unittest.main()