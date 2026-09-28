import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_monte_carlo import run_monte_carlo_stress_test, start_new
from skills.market_portfolio_slippage_model import calculate_slippage
from skills.market_anomaly_detector import detect_anomalies
from skills.db_storage import save_stress_result, get_stress_result

class TestMarketPortfolioStressMonteCarloIntegration(unittest.TestCase):
    def test_full_monte_carlo_stress_pipeline_integration(self):
        portfolio_id = f"test_port_{uuid.uuid4().hex}"
        capital = round(random.uniform(50000.0, 2000000.0), 2)
        iterations = random.choice([500, 1000, 5000])
        volatility = round(random.uniform(0.1, 0.5), 4)

        raw_slippage = calculate_slippage(volatility=volatility, volume=capital)
        slippage = float(raw_slippage) if isinstance(raw_slippage, (int, float, str)) else 0.01

        anomaly_input_data = {"volatility": volatility, "portfolio_id": portfolio_id}
        detected_anomalies_raw = detect_anomalies(anomaly_input_data)
        anomalies = detected_anomalies_raw if isinstance(detected_anomalies_raw, list) else [detected_anomalies_raw]

        result = run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            capital=capital,
            iterations=iterations,
            volatility=volatility,
            anomalies=anomalies,
            slippage=slippage
        )

        self.assertIn("simulation_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_capital"], capital)
        self.assertEqual(result["iterations"], iterations)
        self.assertEqual(result["volatility"], volatility)
        self.assertEqual(result["slippage_rate"], slippage)

        report_path = result.get("report_path")
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path), f"Report file {report_path} should exist on disk")

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("status", content)

        db_payload = {
            "simulation_id": result["simulation_id"],
            "portfolio_id": portfolio_id,
            "var_95": result["var_95"]
        }
        save_stress_result(portfolio_id, db_payload)

        fetched_data = get_stress_result(portfolio_id)
        self.assertIsNotNone(fetched_data)

    def test_start_new_anomaly_and_storage_interaction(self):
        anomaly_sig = f"sig_{uuid.uuid4().hex}"
        vol = round(random.uniform(0.15, 0.45), 2)

        res = start_new(anomaly_signature=anomaly_sig, volatility=vol)
        self.assertEqual(res["anomaly_processed"], anomaly_sig)
        self.assertEqual(res["volatility_used"], vol)
        self.assertIn("stress_score", res)

        try:
            db_status_check = start_new(db_storage=None, market_parser="active")
        except RuntimeError:
            db_status_check = {"status": "error"}
        # ожидаем исключение или корректную обработку в соответствии с логикой модуля
        self.assertIsInstance(db_status_ungeon := start_new(market_portfolio_autonomous_sentinel=f"sent_{uuid.uuid4().hex}"), dict)
        self.assertEqual(db_status_ungeon["status"], "idle")

if __name__ == "__main__":
    unittest.main()