import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import requests

from skills.market_portfolio_stress_diagnostic_hub_v3 import (
    run_diagnostic_hub,
    process_market_stream,
    audit_portfolio_anomalies,
    compute_tax_impact,
    broadcast_stress_alert,
    market_portfolio_stress_diagnostic_hub_v3_execute
)

class TestMarketPortfolioStressDiagnosticHubV3(unittest.TestCase):

    def test_run_diagnostic_hub_success(self):
        db_conn = MagicMock()
        rand_conn = uuid.uuid4().hex
        rand_query = uuid.uuid4().hex
        db_conn.connect.return_value = rand_conn
        db_conn.query.return_value = rand_query

        simulator = MagicMock()
        rand_sim = uuid.uuid4().hex
        simulator.run_simulation.return_value = rand_sim

        mc_engine = MagicMock()
        rand_mc = uuid.uuid4().hex
        mc_engine.simulate.return_value = rand_mc

        target_url = f"http://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"

        mock_response = MagicMock()
        mock_response.status_code = random.choice([200, 201, 400, 500])

        with patch("requests.get", return_value=mock_response) as mock_get:
            res = run_diagnostic_hub(db_conn, simulator, mc_engine, target_url)
            mock_get.assert_called_once_with(target_url, timeout=5)

        self.assertEqual(res["connect"], rand_conn)
        self.assertEqual(res["query"], rand_query)
        self.assertEqual(res["simulation"], rand_sim)
        self.assertEqual(res["monte_carlo"], rand_mc)
        self.assertEqual(res["response_status"], mock_response.status_code)

    def test_run_diagnostic_hub_request_exception(self):
        db_conn = MagicMock()
        simulator = MagicMock()
        mc_engine = MagicMock()
        target_url = f"http://{uuid.uuid4().hex}.net"

        with patch("requests.get", side_effect=requests.exceptions.RequestException):
            res = run_diagnostic_hub(db_conn, simulator, mc_engine, target_url)

        self.assertIsNone(res["response_status"])

    def test_process_market_stream(self):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        parser = MagicMock()
        expected_parsed = uuid.uuid4().hex
        parser.parse_stream.return_value = expected_parsed

        res = process_market_stream(stream_data, parser)
        parser.parse_stream.assert_called_once_with(stream_data)
        self.assertEqual(res, str(expected_parsed))

    def test_audit_portfolio_anomalies(self):
        detector = MagicMock()
        dispatcher = MagicMock()

        anomaly_val = uuid.uuid4().hex
        dispatch_val = uuid.uuid4().hex

        detector.detect.return_value = anomaly_val
        dispatcher.dispatch.return_value = dispatch_val

        res = audit_portfolio_anomalies(detector, dispatcher)
        detector.detect.assert_called_once()
        dispatcher.dispatch.assert_called_once_with(anomaly_val)

        self.assertEqual(res["anomaly"], anomaly_val)
        self.assertEqual(res["dispatched"], dispatch_val)

    def test_compute_tax_impact(self):
        valuation = MagicMock()
        tax_calc = MagicMock()

        curr_val = random.uniform(1000.0, 500000.0)
        cost_basis = random.uniform(500.0, 250000.0)
        tax_res = random.uniform(50.0, 15000.0)

        valuation.get_value.return_value = curr_val
        tax_calc.calculate.return_value = tax_res

        res = compute_tax_impact(valuation, tax_calc, cost_basis)

        valuation.get_value.assert_called_once()
        tax_calc.calculate.assert_called_once_with(curr_val, cost_basis)
        self.assertEqual(res, float(tax_res))

    def test_broadcast_stress_alert(self):
        notifier = MagicMock()
        sync_agent = MagicMock()

        message = uuid.uuid4().hex
        notif_resp = uuid.uuid4().hex
        sync_resp = uuid.uuid4().hex

        notifier.send_message.return_value = notif_resp
        sync_agent.sync.return_value = sync_resp

        res = broadcast_stress_alert(notifier, sync_agent, message)

        notifier.send_message.assert_called_once_with(message)
        sync_agent.sync.assert_called_once_with(message)

        self.assertEqual(res["notifier"], notif_resp)
        self.assertEqual(res["sync"], sync_resp)

    def test_market_portfolio_stress_diagnostic_hub_v3_execute(self):
        portfolio_id = uuid.uuid4().hex
        initial_capital = random.randint(10000, 1000000)
        shock_pct = random.uniform(-50.0, -5.0)
        sim_data = uuid.uuid4().hex
        mc_data = uuid.uuid4().hex

        payload = {
            "portfolio_id": portfolio_id,
            "initial_capital": initial_capital,
            "shock_pct": shock_pct,
            "sim_data": sim_data,
            "mc_data": mc_data
        }

        with patch("skills.market_portfolio_stress_diagnostic_hub_v3.db_storage_client") as mock_db:
            res = market_portfolio_stress_diagnostic_hub_v3_execute(payload)

            self.assertEqual(res["portfolio_id"], portfolio_id)
            self.assertEqual(res["initial_capital"], initial_capital)
            self.assertEqual(res["shock_pct"], shock_pct)
            self.assertEqual(res["sim_data"], sim_data)
            self.assertEqual(res["mc_data"], mc_data)
            self.assertEqual(res["status"], "SUCCESS")
            self.assertIn("diagnostic_id", res)

            diag_id = res["diagnostic_id"]
            mock_db.set.assert_called_once_with(f"stress_diag_{diag_id}", res)

if __name__ == '__main__':
    unittest.main()