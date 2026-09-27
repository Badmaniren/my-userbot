import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_insider_portfolio_hedger_engine import start_new, market_insider_portfolio_hedger_engine


class TestMarketInsiderPortfolioHedgerEngine(unittest.TestCase):

    def test_start_new_db_none(self):
        rand_key = uuid.uuid4().hex
        dependencies = {rand_key: MagicMock()}
        result = start_new(dependencies)
        self.assertIsNone(result)

    def test_start_new_portfolio_none(self):
        mock_db = MagicMock()
        mock_db.fetch_portfolios.return_value = None
        mock_db.fetch_portfolio.return_value = None
        dependencies = {"db_storage": mock_db}
        result = start_new(dependencies)
        self.assertIsNone(result)

    def test_start_new_with_active_portfolios(self):
        mock_db = MagicMock()
        portfolio_data = {uuid.uuid4().hex: random.randint(100, 1000)}
        mock_db.fetch_portfolio.return_value = portfolio_data
        active_portfolios_data = [uuid.uuid4().hex for _ in range(3)]
        mock_db.get_active_portfolios.return_value = active_portfolios_data

        mock_analyzer = MagicMock()
        mock_pipeline = MagicMock()

        dependencies = {
            "db_storage": mock_db,
            "market_insider_anomaly_analyzer": mock_analyzer,
            "market_insider_alert_pipeline": mock_pipeline
        }

        result = start_new(dependencies)
        self.assertEqual(result, {"status": "PROCESSED"})
        mock_analyzer.analyze.assert_called_once_with(activity_Data=active_portfolios_data)
        mock_pipeline.execute_hedge.assert_called_once_with(portfolio_data=active_portfolios_data)

    def test_start_new_with_detector(self):
        mock_db = MagicMock()
        portfolio_id = uuid.uuid4().hex
        portfolio_data = {"id": portfolio_id}
        mock_db.fetch_portfolio.return_value = portfolio_data
        if hasattr(mock_db, "get_active_portfolios"):
            delattr(mock_db, "get_active_portfolios")

        mock_detector = MagicMock()
        dependencies = {
            "db_storage": mock_db,
            "market_anomaly_detector": mock_detector
        }

        result = start_new(dependencies)
        self.assertIn("execution_id", result)
        self.assertEqual(result["portfolio"], portfolio_data)
        mock_detector.evaluate.assert_called_once_with(portfolio=portfolio_data)

    def test_start_new_execution_flow(self):
        mock_db = MagicMock()
        portfolio_id = uuid.uuid4().hex
        portfolio_data = {"portfolio_id": portfolio_id, "value": random.uniform(10500.0, 99999.0)}
        mock_db.fetch_portfolio.return_value = portfolio_data

        with patch("skills.market_insider_portfolio_hedger_engine.str", side_effect=lambda x: str(x)) as _:
            dependencies = {
                "db_storage": mock_db
            }
            result = start_new(dependencies)
            self.assertIn("execution_id", result)
            self.assertEqual(result["portfolio"], portfolio_data)

    def test_hedger_engine_integration_workflow(self):
        portfolio_id = uuid.uuid4().hex
        sim_key = uuid.uuid4().hex
        sim_val = random.randint(1, 100)
        simulation_data = {sim_key: sim_val}
        exec_mode = uuid.uuid4().hex

        with patch("skills.market_insider_portfolio_hedger_engine.db_storage") as mock_db_storage:
            mock_db_storage.initialize_connection = MagicMock()
            mock_db_storage.save_record = MagicMock()

            output = market_insider_portfolio_hedger_engine(
                portfolio_id=portfolio_id,
                simulation_data=simulation_data,
                execution_mode=exec_mode
            )

            self.assertEqual(output["target_portfolio_id"], portfolio_id)
            self.assertEqual(output["simulation"], simulation_data)
            self.assertEqual(output["mode"], exec_mode)
            self.assertEqual(output["status"], "SUCCESS")
            self.assertIn("hedge_execution_id", output)
            mock_db_storage.save_record.assert_called_once()

    def test_market_insider_portfolio_hedger_engine_no_db(self):
        portfolio_id = uuid.uuid4().hex
        simulation_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_insider_portfolio_hedger_engine.db_storage", None):
            output = market_insider_portfolio_hedger_engine(
                portfolio_id=portfolio_id,
                simulation_data=simulation_data
            )
            self.assertEqual(output["target_portfolio_id"], portfolio_id)
            self.assertEqual(output["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()