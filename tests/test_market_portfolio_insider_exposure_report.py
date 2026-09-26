import unittest
from unittest.mock import patch, mock_open, MagicMock
import uuid
import random
import json
import io
from skills.market_portfolio_insider_exposure_report import generate_insider_exposure_report

class TestMarketPortfolioInsiderExposureReport(unittest.TestCase):

    def test_generate_insider_exposure_report_basic(self):
        rand_portfolio = uuid.uuid4().hex
        rand_ticker = f"TICK_{random.randint(100, 999)}"
        rand_report_id = uuid.uuid4().hex
        rand_score = float(random.uniform(1.0, 99.0))

        mock_db = MagicMock()
        mock_tracker = MagicMock()
        mock_detector = MagicMock()

        activity_payload = {"score": rand_score, "data": uuid.uuid4().hex}
        anomaly_payload = {"anomaly": uuid.uuid4().hex}

        with patch("builtins.open", mock_open()) as mock_file, \
             patch("os.makedirs") as mock_mkdirs:

            result = generate_insider_exposure_report(
                db_storage=mock_db,
                market_insider_activity_tracker=mock_tracker,
                market_anomaly_detector=mock_detector,
                portfolio_id=rand_portfolio,
                ticker=rand_ticker,
                activity_payload=activity_payload,
                anomaly_payload=anomaly_payload,
                report_id=rand_report_id
            )

            mock_db.fetch_data.assert_called_once()
            mock_tracker.get_activity.assert_called_once()
            mock_detector.detect.assert_called_once()

            self.assertEqual(result["report_id"], rand_report_id)
            self.assertEqual(result["portfolio_id"], rand_portfolio)
            self.assertEqual(result["ticker"], rand_ticker)
            self.assertEqual(result["exposure_score"], rand_score)
            self.assertEqual(result["activity_payload"], activity_payload)
            self.assertEqual(result["anomaly_payload"], anomaly_payload)
            self.assertEqual(result["status"], "generated")

            mock_mkdirs.assert_called_once_with("reports", exist_ok=True)
            mock_file.assert_called_once_with(f"reports/insider_exposure_{rand_report_id}.json", "w", encoding="utf-8")

    def test_generate_insider_exposure_report_positional_args(self):
        mock_db = MagicMock()
        mock_tracker = MagicMock()
        mock_detector = MagicMock()

        rand_portfolio = uuid.uuid4().hex

        with patch("builtins.open", mock_open()), \
             patch("os.makedirs"):

            result = generate_insider_exposure_report(mock_db, mock_tracker, mock_detector, portfolio_id=rand_portfolio)

            mock_db.fetch_data.assert_called_once()
            mock_tracker.get_activity.assert_called_once()
            mock_detector.detect.assert_called_once()
            self.assertEqual(result["portfolio_id"], rand_portfolio)

    def test_generate_insider_exposure_report_random_anomalies(self):
        rand_score = float(random.uniform(10.0, 50.0))
        rand_report_id = uuid.uuid4().hex

        with patch('skills.market_portfolio_insider_exposure_report.random.uniform', return_value=rand_score), \
             patch("builtins.open", mock_open()), \
             patch("os.makedirs"):

            result = generate_insider_exposure_report(report_id=rand_report_id)
            self.assertEqual(result["exposure_score"], rand_score)
            self.assertEqual(result["report_id"], rand_report_id)

    def test_generate_insider_exposure_report_file_writing(self):
        rand_report_id = uuid.uuid4().hex
        mock_file = mock_open()

        with patch("builtins.open", mock_file) as mock_file_constructor, \
             patch("os.makedirs"):

            generate_insider_exposure_report(report_id=rand_report_id)

            mock_file_constructor.assert_called_once_with(f"reports/insider_exposure_{rand_report_id}.json", "w", encoding="utf-8")
            mock_file.return_value.write.assert_called()

if __name__ == "__main__":
    unittest.main()