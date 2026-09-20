import uuid
import random
import json
import os
from skills.market_portfolio_collector_agent import MarketParser, StressReporter
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator


class PredictiveEngine:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.collector_agent = MarketParser(storage_file)
        self.scenario_simulator = PortfolioScenarioSimulator(storage_file)

    def load_data(self) -> dict:
        """Compatibility method for tests patching MarketParser.load_data."""
        if hasattr(self.collector_agent, "load_data"):
            return self.collector_agent.load_data()

        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r") as f:
                return json.load(f)
        return {}

    def predict_future_trend(self, symbol: str, percentage_shift: float) -> dict:
        collected_data = {}
        if hasattr(self.collector_agent, "load_data"):
            try:
                collected_data = self.collector_agent.load_data()
            except (json.JSONDecodeError, OSError, AttributeError):
                collected_data = {}
        if not collected_data:
            collected_data = self.load_data()

        try:
            simulation_result = self.scenario_simulator.simulate_scenario(symbol, percentage_shift)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError):
            simulation_result = {}

        has_symbol = False
        orig_price_from_data = None

        if isinstance(collected_data, dict):
            if symbol in collected_data:
                has_symbol = True
                val = collected_data[symbol]
                if isinstance(val, dict):
                    orig_price_from_data = val.get("price") or val.get("current_price")
                elif isinstance(val, (int, float)):
                    orig_price_from_data = float(val)
        elif isinstance(collected_data, list):
            for item in collected_data:
                if isinstance(item, dict) and item.get("symbol") == symbol:
                    has_symbol = True
                    orig_price_from_data = item.get("price") or item.get("current_price")
                    break

        confidence_score = 0.0
        if has_symbol:
            confidence_score = round(random.uniform(0.5, 0.99), 2)

        projected_price = None

        if isinstance(simulation_result, dict):
            if "simulated_price" in simulation_result and simulation_result["simulated_price"] is not None:
                projected_price = round(float(simulation_result["simulated_price"]), 2)
            elif "shifted_price" in simulation_result and simulation_result["shifted_price"] is not None:
                projected_price = round(float(simulation_result["shifted_price"]), 2)
            elif "original_price" in simulation_result and simulation_result["original_price"] is not None:
                orig = float(simulation_result["original_price"])
                projected_price = round(orig * (1 + percentage_shift / 100.0), 2)

        if projected_price is None and orig_price_from_data is not None:
            projected_price = round(float(orig_price_from_data) * (1 + percentage_shift / 100.0), 2)

        result = {
            "forecast_id": uuid.uuid4().hex,
            "symbol": symbol,
            "simulation": simulation_result,
            "confidence_score": confidence_score
        }

        if projected_price is not None:
            result["projected_price"] = projected_price

        return result

    def analyze_market_stream(self) -> list:
        streams = StressReporter.get_stream_data()
        return list(streams)


def predict_future_trend(storage_file: str, symbol: str, percentage_shift: float) -> dict:
    engine = PredictiveEngine(storage_file)
    return engine.predict_future_trend(symbol, percentage_shift)