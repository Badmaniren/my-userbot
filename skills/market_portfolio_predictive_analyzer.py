import json
from skills.market_portfolio_collector_agent import MarketParser
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator


class PredictiveAnalyzer:
    def __init__(self, storage_file="market_data.json"):
        self.storage_file = storage_file
        self.market_parser = MarketParser(storage_file)
        self.simulator = PortfolioScenarioSimulator(storage_file)

    def _read_storage(self):
        """Внутренний метод для безопасного чтения JSON-хранилища."""
        if hasattr(self.market_parser, "load_data"):
            data = self.market_parser.load_data(self.storage_file)
            if data:
                return data
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def collect_and_simulate(self, url, symbol, percentage_shift):
        price = self.market_parser.fetch_price(url)
        self.market_parser.fetch_and_store(symbol, price)
        return self.simulator.simulate_scenario(symbol, percentage_shift)

    def run_retrospective_stress_analysis(self, symbol, shifts):
        return self.simulator.run_stress_test(symbol, shifts)

    def analyze_and_predict(self, symbol, shift):
        data = self._read_storage()

        original_price = 0.0
        if isinstance(data, dict):
            val = data.get(symbol)
            if isinstance(val, dict):
                original_price = float(val.get("price", 100.0))
            elif isinstance(val, (int, float)):
                original_price = float(val)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("symbol") == symbol:
                    p = item.get("price", 100.0)
                    if isinstance(p, dict):
                        original_price = float(p.get("price", 100.0))
                    elif isinstance(p, (int, float)):
                        original_price = float(p)
                    break

        if original_price == 0.0:
            original_price = 100.0

        predicted_value = original_price * (1 + shift)
        return {
            "symbol": symbol,
            "original_price": original_price,
            "predicted_value": predicted_value,
            "status": "success"
        }

    def run_comprehensive_forecast(self, symbol, shifts):
        report = []
        for shift in shifts:
            sim_res = self.simulator.simulate_scenario(symbol, shift * 100)
            proj = 100.0
            if isinstance(sim_res, dict):
                proj = sim_res.get("simulated_value") or sim_res.get("simulated_price") or 100.0
            report.append({
                "scenario_shift": shift,
                "projected_price": proj
            })
        return report


def run_predictive_analysis(symbol, url, percentage_shift, storage_file="market_data.json"):
    parser = MarketParser(storage_file)
    simulator = PortfolioScenarioSimulator(storage_file)

    current_price = parser.fetch_price(url)
    parser.fetch_and_store(symbol, current_price)

    sim_result = simulator.simulate_scenario(symbol, percentage_shift)
    if isinstance(sim_result, dict):
        sim_result["status"] = "success"
        sim_result["symbol"] = symbol
        sim_result["current_price"] = current_price
        return sim_result

    return {
        "status": "success",
        "symbol": symbol,
        "current_price": current_price,
        "token": "pipeline_token"
    }