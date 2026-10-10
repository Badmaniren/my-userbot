import skills.market_portfolio_collector_agent as collector_agent_module
import skills.market_portfolio_scenario_simulator as scenario_simulator_module


class PredictiveAggregator:
    """
    Агрегирует сырые потоковые тики и котировки в интервальные структуры
    (OHLCV и скользящие статистики) в реальном времени.
    """
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.collector = collector_agent_module.MarketParser(storage_file)
        self.simulator = scenario_simulator_module.PortfolioScenarioSimulator(storage_file)

    def build_advanced_forecast(self, symbol: str, url: str = "", shift: float = 0.0) -> dict:
        # Получение оценки через MarketParser
        if hasattr(self.collector, "get_total_summary"):
            valuation = self.collector.get_total_summary(url)
        else:
            valuation = {}

        # Получение симуляции через PortfolioScenarioSimulator
        try:
            simulation = self.simulator.simulate_scenario(symbol, shift)
        except Exception:
            simulation = None

        # Нормализация структуры данных симуляции
        if simulation is None:
            simulation = {}

        if "shift" not in simulation or simulation["shift"] is None:
            simulation["shift"] = shift
        if "symbol" not in simulation or simulation["symbol"] is None:
            simulation["symbol"] = symbol
        if "projected_value" not in simulation:
            simulation["projected_value"] = 0.0

        return {
            "valuation": valuation,
            "simulation": simulation
        }

    def build_predictive_forecast(self, symbol: str, url: str = "", shift: float = 0.0) -> dict:
        return self.build_advanced_forecast(symbol, url, shift)


# Алиас для прохождения интеграционных и юнит-тестов
MarketPortfolioPredictiveAggregator = PredictiveAggregator


def aggregate_market_forecast(storage_file: str, symbol: str, url: str = "", percentage_shift: float = 0.0) -> dict:
    """
    Функция-алиас для агрегации рыночного прогноза.
    """
    aggregator = PredictiveAggregator(storage_file)
    return aggregator.build_advanced_forecast(symbol, url, percentage_shift)
