import unittest
from unittest.mock import patch, MagicMock
import uuid
import random

class TestMarketPortfolioStressReportSynthesizer(unittest.TestCase):

    def test_synthesizer_class_success(self):
        from skills.market_portfolio_stress_report_synthesizer import MarketPortfolioStressReportSynthesizer

        portfolio_id = uuid.uuid4().hex
        report_id = uuid.uuid4().hex
        stress_matrix_data = {
            "report_id": report_id,
            "metrics": random.random()
        }

        mock_storage = MagicMock()
        synthesizer = MarketPortfolioStressReportSynthesizer(dependencies={'db_storage': mock_storage})

        result = synthesizer.synthesize_report(portfolio_id, stress_matrix_data)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["report_id"], report_id)
        self.assertEqual(result["status"], "SYNTHESIZED")
        self.assertIn("entropy", result)
        mock_storage.save_report.assert_called_once_with(report_id, stress_matrix_data)

    def test_synthesizer_class_invalid_input(self):
        from skills.market_portfolio_stress_report_synthesizer import MarketPortfolioStressReportSynthesizer

        synthesizer = MarketPortfolioStressReportSynthesizer()

        with self.assertRaises(ValueError):
            synthesizer.synthesize_report("", {})

        with self.assertRaises(ValueError):
            synthesizer.synthesize_report(uuid.uuid4().hex, {})

    def test_synthesizer_function_success(self):
        from skills.market_portfolio_stress_report_synthesizer import market_portfolio_stress_report_synthesizer

        portfolio_id = uuid.uuid4().hex
        report_id = uuid.uuid4().hex
        matrix_status = uuid.uuid4().hex
        iterations = random.randint(1, 1000)
        mean_outcome = random.uniform(-100.0, 100.0)

        payload = {
            "portfolio_id": portfolio_id,
            "report_id": report_id,
            "matrix_evaluation": {"status": matrix_status},
            "monte_carlo_simulation": {
                "iterations": iterations,
                "mean_outcome": mean_outcome
            }
        }

        with patch("skills.market_portfolio_stress_report_synthesizer.db_storage") as mock_db:
            result = market_portfolio_stress_report_synthesizer(payload)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["report_id"], report_id)
            self.assertEqual(result["status"], "SYNTHESIZED")
            self.assertEqual(result["aggregated_metrics"]["matrix_status"], matrix_status)
            self.assertEqual(result["aggregated_metrics"]["mc_simulations"], iterations)
            self.assertEqual(result["aggregated_metrics"]["mean_outcome"], mean_outcome)
            self.assertIn("entropy", result)

            mock_db.assert_called_once()
            args, _ = mock_db.call_args
            self.assertEqual(args[0]["action"], "save")
            self.assertEqual(args[0]["table"], "stress_reports")
            self.assertEqual(args[0]["report_id"], report_id)
            self.assertEqual(args[0]["data"], result)

    def test_synthesizer_function_invalid_payload(self):
        from skills.market_portfolio_stress_report_synthesizer import market_portfolio_stress_report_synthesizer

        with self.assertRaises(ValueError):
            market_portfolio_stress_report_synthesizer(None)

        with self.assertRaises(ValueError):
            market_portfolio_stress_report_synthesizer([])

        with self.assertRaises(ValueError):
            market_portfolio_stress_report_synthesizer({})

        with self.assertRaises(ValueError):
            market_portfolio_stress_report_synthesizer({"portfolio_id": uuid.uuid4().hex})

if __name__ == "__main__":
    unittest.main()