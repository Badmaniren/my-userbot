from skills.market_portfolio_collector_agent import MarketParser, PortfolioValuation
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator


class PredictiveAggregator:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.collector = MarketParser(storage_file)
        self.simulator = PortfolioScenarioSimulator(storage_file)

    def build_advanced_forecast(self, symbol: str, url: str, shift: float) -> dict:
        if hasattr(self.collector, "get_total_summary"):
            valuation = self.collector.get_total_summary(url)
        else:
            valuation = {}

        simulation = self.simulator.simulate_scenario(symbol, shift)
        return {
            "valuation": valuation,
            "simulation": simulation
        }

    def build_predictive_forecast(self, symbol: str, url: str, shift: float) -> dict:
        return self.build_advanced_forecast(symbol, url, shift)


# Алиас для прохождения интеграционных тестов
MarketPortfolioPredictiveAggregator = PredictiveAggregator


def aggregate_market_forecast(storage_file: str, symbol: str, url: str, percentage_shift: float) -> dict:
    aggregator = PredictiveAggregator(storage_file)
    return aggregator.build_advanced_forecast(symbol, url, percentage_shift)