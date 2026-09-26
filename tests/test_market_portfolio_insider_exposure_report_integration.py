import unittest
import os
import uuid
import random
from skills.market_portfolio_insider_exposure_report import generate_insider_exposure_report
from skills.db_storage import save_report_state, get_report_state
from skills.market_insider_activity_tracker import track_insider_activity
from skills.market_anomaly_detector import detect_market_anomalies

class TestMarketPortfolioInsiderExposureReportIntegration(unittest.TestCase):
    def test_generate_insider_exposure_report_integration(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        rand_ticker = random.choice(["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"])
        rand_score = round(random.uniform(10.0, 95.5), 2)

        activity_payload = {
            "score": rand_score,
            "insider_transactions_count": random.randint(1, 15)
        }
        anomaly_payload = {
            "anomaly_detected": True,
            "deviation_sigma": round(random.uniform(2.0, 5.0), 2)
        }

        result = generate_insider_exposure_report(
            db_storage=None,
            market_insider_activity_tracker=None,
            market_anomaly_detector=None,
            portfolio_id=rand_portfolio_id,
            ticker=rand_ticker,
            activity_payload=activity_payload,
            anomaly_payload=anomaly_payload
        )

        self.assertIsInstance(result, dict)
        self.assertIn("report_id", result)
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["ticker"], rand_ticker)
        self.assertEqual(result["exposure_score"], rand_score)
        self.assertEqual(result["activity_payload"], activity_payload)
        self.assertEqual(result["anomaly_payload"], anomaly_payload)

        report_id = result["report_id"]
        report_file_path = f"reports/insider_exposure_{report_id}.json"

        self.assertTrue(os.path.exists(report_file_path))

        if os.path.exists(report_file_path):
            os.remove(report_file_path)

if __name__ == "__main__":
    unittest.main()