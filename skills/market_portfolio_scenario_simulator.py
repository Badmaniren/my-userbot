import json
import os

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
        
        # Обработка структуры данных (поддержка разных форматов из тестов)
        target = None
        if symbol in data:
            target = data[symbol]
        elif "assets" in data:
            target = next((item for item in data["assets"] if item.get("symbol") == symbol), None)
        elif data.get("symbol") == symbol:
            target = data
        
        if not target:
            raise KeyError(f"Symbol {symbol} not found")

        current_price = target.get("current_price") or target.get("price")
        quantity = target.get("quantity") or target.get("shares")
        
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
            res = self.simulate_scenario(symbol, shift)
            report.append({
                "shift_percentage": shift,
                "resulting_valuation": res["simulated_price"]
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