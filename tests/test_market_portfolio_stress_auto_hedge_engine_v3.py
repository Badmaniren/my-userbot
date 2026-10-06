import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import datetime

from skills.market_portfolio_stress_auto_hedge_engine_v3 import start_new, StressAutoHedgeEngine

class TestMarketPortfolioStressAutoHedgeEngineV3(unittest.TestCase):

    def test_start_new_success(self):
        rand_portfolio_id = str(uuid.uuid4())
        rand_scenario_name = f"scenario_{uuid.uuid4().hex[:8]}"
        rand_volume = round(random.uniform(100.0, 10000.0), 2)
        rand_result_id = str(uuid.uuid4())

        mock_metrics = {
            "portfolio_id": rand_portfolio_id,
            "scenario": rand_scenario_name,
            "volume": rand_volume
        }
        mock_hedge_result = {"status": "success", "hedge_id": rand_result_id}

        with patch("skills.market_portfolio_stress_auto_hedge_engine_v3.db_storage") as mock_db:
            mock_db.fetch_stress_metrics.return_value = mock_metrics
            mock_db.execute_hedge_action.return_value = mock_hedge_result

            result = start_new(rand_portfolio_id, rand_scenario_name)

            mock_db.fetch_stress_metrics.assert_called_once_with(rand_portfolio_id, rand_scenario_name)
            mock_db.execute_hedge_action.assert_called_once_with(mock_metrics)
            self.assertEqual(result, mock_hedge_result)

    def test_start_new_metrics_not_found(self):
        rand_portfolio_id = str(uuid.uuid4())
        rand_scenario_name = f"scenario_{uuid.uuid4().hex[:8]}"

        with patch("skills.market_portfolio_stress_auto_hedge_engine_v3.db_storage") as mock_db:
            mock_db.fetch_stress_metrics.return_value = None

            with self.assertRaises(ValueError) as ctx:
                start_new(rand_portfolio_id, rand_scenario_name)

            self.assertEqual(str(ctx.exception), "Metrics data not found")
            mock_db.fetch_stress_metrics.assert_called_once_with(rand_portfolio_id, rand_scenario_name)
            mock_db.execute_hedge_action.assert_not_called()

    def test_stress_auto_hedge_engine_execute_hedge_sequence(self):
        rand_portfolio_id = str(uuid.uuid4())
        rand_scenario_id = str(uuid.uuid4())
        rand_state_val = random.randint(10, 100)

        mock_db = MagicMock()
        mock_db.get_portfolio_state.return_value = {"state": rand_state_val}

        engine = StressAutoHedgeEngine(mock_db)
        result = engine.execute_hedge_sequence(rand_portfolio_id, rand_scenario_id)

        mock_db.get_portfolio_state.assert_called_once_with(rand_portfolio_id)
        mock_db.save_hedge_record.assert_called_once()
        saved_record = mock_db.save_hedge_record.call_args[0][0]

        self.assertEqual(saved_record["portfolio_id"], rand_portfolio_id)
        self.assertEqual(saved_record["scenario_id"], rand_scenario_id)
        self.assertEqual(saved_record["status"], "executed")
        self.assertIn("hedge_order_id", saved_record)

        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["hedge_order_id"], saved_record["hedge_order_id"])

    def test_stress_auto_hedge_engine_run_audit_export(self):
        rand_portfolio_id = str(uuid.uuid4())
        rand_filename = f"audit_{uuid.uuid4().hex}.log"
        rand_audit_data = {"event": uuid.uuid4().hex, "risk_score": random.random()}

        mock_db = MagicMock()
        mock_db.get_audit_data.return_value = rand_audit_data

        engine = StressAutoHedgeEngine(mock_db)

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            engine.run_audit_export(rand_portfolio_id, rand_filename)

            mock_db.get_audit_data.assert_called_once_with(rand_portfolio_id)
            mock_open.assert_called_once_with(rand_filename, 'w')
            mock_file.write.assert_called_once_with(str(rand_audit_data))

    def test_stress_auto_hedge_engine_verify_compliance(self):
        rand_portfolio_id = str(uuid.uuid4())
        mock_db = MagicMock()

        engine = StressAutoHedgeEngine(mock_db)
        compliance = engine.verify_compliance(rand_portfolio_id)

        self.assertTrue(compliance["is_compliant"])
        self.assertEqual(compliance["portfolio_id"], rand_portfolio_id)
        self.assertIn("timestamp", compliance)
        
        datetime.datetime.fromisoformat(compliance["timestamp"])

if __name__ == "__main__":
    unittest.main()