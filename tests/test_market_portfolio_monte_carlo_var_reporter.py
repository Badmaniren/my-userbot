import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.market_portfolio_monte_carlo_var_reporter import MarketPortfolioMonteCarloVarReporter

class TestMarketPortfolioMonteCarloVarReporter(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.monte_carlo_engine = MagicMock()
        self.visualizer = MagicMock()
        self.reporter = MarketPortfolioMonteCarloVarReporter(
            db_storage=self.db_storage,
            market_portfolio_stress_monte_carlo_engine=self.monte_carlo_engine,
            market_portfolio_visualizer_v2=self.visualizer
        )

    def test_generate_var_report_success(self):
        portfolio_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        time_horizon = random.randint(1, 30)
        simulations_count = random.randint(1000, 50000)

        expected_var = -round(random.uniform(1000.0, 50000.0), 2)
        expected_es = -round(abs(expected_var) * random.uniform(1.1, 1.5), 2)

        sim_data = [random.gauss(0, 1) for _ in range(100)]
        bytes_garbage = io.BytesIO(bytes(random.choices(string.ascii_letters.encode(), k=64)))

        self.monte_carlo_engine.run_simulations.return_value = {
            "simulations": sim_data,
            "raw_stream": bytes_garbage
        }

        self.db_storage.fetch_portfolio.return_value = {
            "portfolio_id": portfolio_id,
            "initial_value": round(random.uniform(100000.0, 1000000.0), 2)
        }

        with patch('skills.market_portfolio_monte_carlo_var_reporter.uuid') as mock_uuid:
            generated_report_id = str(uuid.uuid4())
            mock_uuid.uuid4.return_value = uuid.UUID(generated_report_id)

            report = self.reporter.generate_report(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                simulations_count=simulations_count
            )

            self.assertIsInstance(report, dict)
            self.assertEqual(report.get("report_id"), generated_report_id)
            self.assertEqual(report.get("portfolio_id"), portfolio_id)
            self.assertEqual(report.get("confidence_level"), confidence_level)
            self.assertEqual(report.get("time_horizon"), time_horizon)
            self.assertIn("var_value", report)
            self.assertIn("expected_shortfall", report)

            self.db_storage.save_report.assert_called_once()
            saved_arg = self.db_storage.save_report.call_args[0][0]
            self.assertEqual(saved_arg["report_id"], generated_report_id)

    def test_generate_var_report_invalid_portfolio(self):
        bad_portfolio_id = str(uuid.uuid4())
        self.db_storage.fetch_portfolio.return_value = None

        confidence_level = round(random.uniform(0.90, 0.99), 2)
        time_horizon = random.randint(1, 10)
        simulations_count = random.randint(500, 1000)

        with self.assertRaises(ValueError) as context:
            self.reporter.generate_report(
                portfolio_id=bad_portfolio_id,
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                simulations_count=simulations_count
            )

        self.assertIn(bad_portfolio_id, str(context.exception))
        self.monte_carlo_engine.run_simulations.assert_not_called()

    def test_export_var_report_stream(self):
        report_id = str(uuid.uuid4())
        mock_stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')

        self.db_storage.get_report_stream.return_value = io.BytesIO(mock_stream_data)

        with patch('requests.post') as mock_post:
            target_url = f"https://{uuid.uuid4().hex}.com/webhook"
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "accepted"}

            result = self.reporter.export_report_to_webhook(report_id, target_url)

            self.assertTrue(result)
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], target_url)
            self.db_storage.get_report_stream.assert_called_once_with(report_id)

    def test_calculate_metrics_edge_case_empty_simulations(self):
        empty_sims = []
        confidence = 0.95

        with self.assertRaises(ZeroDivisionError):
            self.reporter._calculate_var_and_es(empty_sims, confidence)

    def test_visualize_monte_carlo_distribution(self):
        simulations = [random.gauss(100, 15) for _ in range(random.randint(50, 200))]
        output_filename = f"report_{uuid.uuid4().hex}.png"

        self.visualizer.plot_distribution.return_value = output_filename

        file_path = self.reporter.generate_distribution_plot(simulations)

        self.assertEqual(file_path, output_filename)
        self.visualizer.plot_distribution.assert_called_once_with(simulations)
