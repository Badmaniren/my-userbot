import json
import os

from skills.market_parser import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation

class PortfolioScenarioSimulator:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def load_data(self, storage_file):
        try:
            with open(storage_file, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {}

    def simulate_scenario(self, symbol, percentage):
        data = self.load_data(self.storage_file)
        
        target = None
        if isinstance(data, dict):
            if symbol in data:
                target = data[symbol]
            elif "assets" in data and isinstance(data["assets"], list):
                target = next((item for item in data["assets"] if item.get("symbol") == symbol), None)
            elif "holdings" in data and isinstance(data["holdings"], list):
                target = next((item for item in data["holdings"] if item.get("symbol") == symbol), None)
            elif data.get("symbol") == symbol:
                target = data
        elif isinstance(data, list):
            target = next((item for item in data if isinstance(item, dict) and item.get("symbol") == symbol), None)
        
        if target is None:
            raise KeyError(f"Symbol {symbol} not found")

        current_price = 0.0
        quantity = 0.0

        if isinstance(target, dict):
            current_price = float(target.get("current_price") or target.get("price") or target.get("close") or 0.0)
            quantity = float(target.get("quantity") or target.get("shares") or 0.0)
        elif isinstance(target, list) and len(target) > 0:
            last_item = target[-1]
            if isinstance(last_item, dict):
                current_price = float(last_item.get("current_price") or last_item.get("price") or last_item.get("close") or 0.0)
                quantity = float(last_item.get("quantity") or last_item.get("shares") or 0.0)
            elif isinstance(last_item, (int, float)):
                current_price = float(last_item)
        elif isinstance(target, (int, float)):
            current_price = float(target)

        simulated_price = current_price * (1 + percentage / 100.0)
        pnl_impact = (simulated_price - current_price) * quantity
        
        return {
            "symbol": symbol,
            "simulated_price": simulated_price,
            "pnl_impact": pnl_impact,
            "portfolio_value_delta": pnl_impact
        }

    def run_stress_test(self, symbol, shifts):
        report = []
        for shift in shifts:
            try:
                res = self.simulate_scenario(symbol, shift)
                resulting_valuation = res["simulated_price"]
            except Exception:
                resulting_valuation = 0.0
            report.append({
                "shift_percentage": shift,
                "resulting_valuation": resulting_valuation
            })
        return report

def simulate_market_scenario(storage_file, symbol, percentage):
    simulator = PortfolioScenarioSimulator(storage_file)
    return simulator.simulate_scenario(symbol, percentage)

def run_stress_test(storage_file, symbol, range_min, range_max, step):
    simulator = PortfolioScenarioSimulator(storage_file)
    shifts = [float(x) for x in range(int(range_min), int(range_max) + 1, step)]
    scenarios = simulator.run_stress_test(symbol, shifts)
    return {
        "symbol": symbol,
        "scenarios": scenarios
    }