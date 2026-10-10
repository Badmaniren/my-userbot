import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_predictive_var_stress_validation_nexus import (
    MarketPortfolioPredictiveVarStressValidationNexus
)
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_backtester import MarketPortfolioBacktester


class TestMarketPortfolioPredictiveVarStressValidationNexus(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.extractor_mock = MagicMock()
        self.anomaly_detector_mock = MagicMock()

        self.var_engine = PredictiveVarEngine(
            db_storage=self.db_storage_mock,
            extractor_tool=self.extractor_mock,
            market_anomaly_detector=self.anomaly_detector_mock
        )

        self.random_filepath = f"data_{uuid.uuid4().hex}.csv"
        self.backtester = MarketPortfolioBacktester(filepath=self.random_filepath)

        self.nexus = MarketPortfolioPredictiveVarStressValidationNexus(
            var_engine=self.var_engine,
            backtester=self.backtester
        )

    def test_nexus_initialization_and_composition(self):
        self.assertIsInstance(self.nexus.var_engine, PredictiveVarEngine)
        self.assertIsInstance(self.nexus.backtester, MarketPortfolioBacktester)

    def test_run_comprehensive_validation_nexus(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        initial_capital = round(random.uniform(10000.0, 1000000.0), 2)
        portfolio_value = round(random.uniform(50000.0, 5000000.0), 2)
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        horizon_days = random.randint(1, 30)
        simulations = random.randint(100, 5000)
        iterations = random.randint(10, 100)

        random_equity = [round(initial_capital + random.uniform(-1000, 2000), 2) for _ in range(10)]
        expected_var_result = round(random.uniform(1000.0, 50000.0), 2)
        expected_drawdown = round(random.uniform(0.01, 0.35), 4)

        with patch.object(self.var_engine, 'calculate_predictive_var', return_value=expected_var_result) as mock_var, \
             patch.object(self.backtester, 'run_backtest', return_value=random_equity) as mock_backtest, \
             patch.object(self.backtester, 'calculate_maximum_drawdown', return_value=expected_drawdown) as mock_dd:

            result = self.nexus.run_comprehensive_validation(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                symbol=symbol,
                initial_capital=initial_capital,
                portfolio_value=portfolio_value,
                confidence_level=confidence_level,
                horizon_days=horizon_days,
                simulations=simulations,
                iterations=iterations
            )

            mock_var.assert_called_once_with(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params={},
                iterations=iterations
            )
            mock_backtest.assert_called_once()
            mock_dd.assert_called_once_with(random_equity)

            self.assertIn("var_result", result)
            self.assertIn("max_drawdown", result)
            self.assertEqual(result["var_result"], expected_var_result)
            self.assertEqual(result["max_drawdown"], expected_drawdown)

    def test_nexus_stream_validation_integration(self):
        stream_id = uuid.uuid4().hex
        random_bytes = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream_mock = io.BytesIO(random_bytes)

        with patch.object(self.var_engine, 'process_market_stream', return_value=True) as mock_stream_proc:
            validation_status = self.nexus.validate_market_stream_nexus(stream_mock)

            mock_stream_proc.assert_called_once_with(stream_mock)
            self.assertTrue(validation_status)

    def test_nexus_audit_export_pipeline(self):
        report_id = uuid.uuid4().hex
        loss_limit = round(random.uniform(10000.0, 999999.0), 2)
        expected_audit_payload = {
            "report_id": report_id,
            "loss_limit": loss_limit,
            "status": uuid.uuid4().hex
        }

        with patch.object(self.var_engine, 'export_predictive_audit_report', return_value=expected_audit_payload) as mock_export:
            audit_data = self.nexus.generate_audit_report(report_id=report_id, loss_limit=loss_limit)

            mock_export.assert_called_once_with(report_id=report_id, loss_limit=loss_limit)
            self.assertEqual(audit_data["report_id"], report_id)
            self.assertEqual(audit_data["loss_limit"], loss_limit)


if __name__ == '__main__':
    unittest.main()