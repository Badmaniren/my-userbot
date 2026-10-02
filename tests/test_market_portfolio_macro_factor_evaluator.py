import unittest
from unittest.mock import MagicMock, patch
import uuid
import random

class TestMarketPortfolioMacroFactorEvaluator(unittest.TestCase):
    def test_start_new_full_flow(self):
        rnd_factor = uuid.uuid4().hex[:8]
        rnd_inflation = round(random.uniform(0.01, 0.15), 4)
        rnd_rate = round(random.uniform(0.005, 0.1), 4)
        rnd_gdp = round(random.uniform(-0.05, 0.08), 4)

        mock_parser = MagicMock()
        mock_db = MagicMock()
        mock_scenario = MagicMock()
        mock_scenario.simulate.return_value = {
            "factor": rnd_factor,
            "inflation": rnd_inflation,
            "interest_rate": rnd_rate,
            "gdp_growth": rnd_gdp,
            "status": "simulated"
        }

        from skills.market_portfolio_macro_factor_evaluator import start_new

        res = start_new(
            market_parser=mock_parser,
            db_storage=mock_db,
            market_portfolio_scenario_simulator=mock_scenario
        )

        mock_parser.parse_stream.assert_called_once()
        mock_db.save_audit_log.assert_called_once()
        mock_scenario.simulate.assert_called_once()
        self.assertEqual(res["factor"], rnd_factor)
        self.assertEqual(res["inflation"], rnd_inflation)
        self.assertEqual(res["status"], "simulated")

    def test_start_new_defaults(self):
        from skills.market_portfolio_macro_factor_evaluator import start_new
        res = start_new()
        self.assertEqual(res["status"], "evaluated")
        self.assertIn("inflation", res)
        self.assertIn("interest_rate", res)
        self.assertIn("gdp_growth", res)

    def test_evaluator_class(self):
        rnd_portfolio = uuid.uuid4().hex
        rnd_inf = round(random.uniform(0.0, 0.2), 2)
        rnd_rate = round(random.uniform(0.0, 0.15), 2)
        rnd_gdp = round(random.uniform(-0.1, 0.1), 2)

        with patch("skills.market_portfolio_macro_factor_evaluator.db_storage") as mock_db_storage:
            from skills.market_portfolio_macro_factor_evaluator import market_portfolio_macro_factor_evaluator
            result = market_portfolio_macro_factor_evaluator.evaluate(
                portfolio_id=rnd_portfolio,
                inflation=rnd_inf,
                interest_rate=rnd_rate,
                gdp_growth=rnd_gdp
            )

            self.assertEqual(result["portfolio_id"], rnd_portfolio)
            self.assertEqual(result["inflation"], rnd_inf)
            self.assertEqual(result["interest_rate"], rnd_rate)
            self.assertEqual(result["gdp_growth"], rnd_gdp)
            self.assertEqual(result["status"], "evaluated")
            self.assertTrue(result["evaluation_id"].startswith("eval_"))
            mock_db_storage.save_record.assert_called_once()

if __name__ == "__main__":
    unittest.main()