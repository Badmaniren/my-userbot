import unittest
import uuid
import random
from typing import Dict, Any

from skills.market_insider_portfolio_hedger_engine import (
    start_new,
    market_insider_portfolio_hedger_engine
)
from skills import (
    db_storage,
    market_insider_activity_tracker,
    market_insider_anomaly_analyzer,
    market_portfolio_strategy_optimizer,
    market_portfolio_scenario_simulator
)


class RealDatabaseStub:
    def __init__(self, portfolio_data: Dict[str, Any], active_portfolios: list):
        self.portfolio_data = portfolio_data
        self.active_portfolios = active_portfolios
        self.saved_records = {}
        self.connection_initialized = False

    def fetch_portfolio(self) -> Dict[str, Any]:
        return self.portfolio_data

    def get_active_portfolios(self) -> list:
        return self.active_portfolios

    def initialize_connection(self):
        self.connection_initialized = True

    def save_record(self, record_id: str, data: Dict[str, Any]):
        self.saved_records[record_id] = data


class RealAnalyzerStub:
    def __init__(self):
        self.analyzed_data = None

    def analyze(self, activity_Data: Any):
        self.analyzed_data = activity_Data


class RealPipelineStub:
    def __init__(self):
        self.hedged_data = None

    def execute_hedge(self, portfolio_data: Any):
        self.hedged_data = portfolio_data


class RealDetectorStub:
    def __init__(self):
        self.evaluated_portfolio = None

    def evaluate(self, portfolio: Any):
        self.evaluated_portfolio = portfolio


class TestMarketInsiderPortfolioHedgerEngineIntegration(unittest.TestCase):

    def test_start_new_integration_flow(self):
        rand_val = random.randint(1000, 9999)
        portfolio_id = f"port-{uuid.uuid4()}-{rand_val}"

        portfolio_payload = {
            "portfolio_id": portfolio_id,
            "assets": ["AAPL", "TSLA", "BTC"],
            "valuation": float(rand_val * 100)
        }

        active_portfolios_payload = [
            {"id": portfolio_id, "risk_score": random.random()}
        ]

        db_stub = RealDatabaseStub(portfolio_data=portfolio_payload, active_portfolios=active_portfolios_payload)
        analyzer_stub = RealAnalyzerStub()
        pipeline_stub = RealPipelineStub()
        detector_stub = RealDetectorStub()

        dependencies = {
            "db_storage": db_stub,
            "market_insider_anomaly_analyzer": analyzer_stub,
            "market_insider_alert_pipeline": pipeline_stub,
            "market_anomaly_detector": detector_stub
        }

        result = start_new(dependencies)

        self.assertIsNotNone(result)
        self.assertEqual(result.get("status"), "PROCESSED")
        self.assertEqual(analyzer_stub.analyzed_data, active_portfolios_payload)
        self.assertEqual(pipeline_stub.hedged_data, active_portfolios_payload)
        self.assertIsNone(detector_stub.evaluated_portfolio)

    def test_market_insider_portfolio_hedger_engine_execution(self):
        rand_val = random.randint(1, 100000)
        target_portfolio_id = f"target-p-{uuid.uuid4()}-{rand_val}"

        simulation_payload = {
            "scenario": "market_crash_drop",
            "shock_percentage": float(random.randint(5, 25)),
            "simulation_seed": rand_val
        }

        modes = ["live", "dry_run", "backtest"]
        chosen_mode = random.choice(modes)

        output = market_insider_portfolio_hedger_engine(
            portfolio_id=target_portfolio_id,
            simulation_data=simulation_payload,
            execution_mode=chosen_mode
        )

        self.assertIsInstance(output, dict)
        self.assertEqual(output.get("target_portfolio_id"), target_portfolio_id)
        self.assertEqual(output.get("mode"), chosen_mode)
        self.assertEqual(output.get("simulation"), simulation_payload)
        self.assertEqual(output.get("status"), "SUCCESS")

        hedge_execution_id = output.get("hedge_execution_id")
        self.assertIsNotNone(hedge_execution_id)
        self.assertTrue(len(str(hedge_execution_id)) > 0)


if __name__ == "__main__":
    unittest.main()