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

        if isinstance(target, list):
            if not target:
                raise KeyError(f"Symbol {symbol} has no records")
            latest = target[-1]
            if isinstance(latest, dict):
                current_price = latest.get("current_price") or latest.get("price") or 0.0
                quantity = latest.get("quantity") or latest.get("shares") or 0.0
            elif isinstance(latest, (int, float)):
                current_price = float(latest)
                quantity = 1.0
            else:
                current_price = 0.0
                quantity = 0.0
        elif isinstance(target, dict):
            current_price = target.get("current_price") or target.get("price") or 0.0
            quantity = target.get("quantity") or target.get("shares") or 0.0
        elif isinstance(target, (int, float)):
            current_price = float(target)
            quantity = 1.0
        else:
            current_price = 0.0
            quantity = 0.0
        
        simulated_price = current_price * (1 + percentage / 100.0)
        pnl_impact = (simulated_price - current_price) * quantity
        
        return {
            "symbol": symbol,
            "simulated_price": simulated_price,
            "pnl_impact": pnl_impact,
            "portfolio_value_delta": pnl_impact
        }

    def run_stress_test(self, symbol, shifts):
        if isinstance(shifts, (int, float)):
            shifts = [shifts]
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