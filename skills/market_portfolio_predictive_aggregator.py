import skills.market_portfolio_collector_agent as collector_module
import skills.market_portfolio_scenario_simulator as simulator_module


class PredictiveAggregator:
    """
    Центральный узел для сбора и нормализации метрик риска.
    Объединяет данные оценки портфеля и результаты сценарного моделирования.
    """
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.collector = collector_module.MarketParser(storage_file)
        self.valuation_agent = collector_module.PortfolioValuation(storage_file) if hasattr(collector_module, "PortfolioValuation") else None
        self.simulator = simulator_module.PortfolioScenarioSimulator(storage_file)

    def build_advanced_forecast(self, symbol: str, url: str, shift: float) -> dict:
        # Получение оценки портфеля
        valuation = {}
        if hasattr(self.collector, "get_total_summary"):
            valuation = self.collector.get_total_summary(url)
        elif self.valuation_agent and hasattr(self.valuation_agent, "get_total_summary"):
            valuation = self.valuation_agent.get_total_summary(url)

        # Получение данных симуляции с обработкой состояний
        try:
            simulation = self.simulator.simulate_scenario(symbol, shift)
        except KeyError:
            simulation = None

        if simulation is None:
            simulation = {}

        # Нормализация данных симуляции
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

    def build_predictive_forecast(self, symbol: str, url: str, shift: float) -> dict:
        """
        Алиас для построения предиктивного прогноза.
        """
        return self.build_advanced_forecast(symbol, url, shift)


# Алиас для обеспечения обратной совместимости с интеграционными тестами
MarketPortfolioPredictiveAggregator = PredictiveAggregator


def aggregate_market_forecast(storage_file: str, symbol: str, url: str, percentage_shift: float) -> dict:
    """
    Функция-обертка для агрегации рыночного прогноза.
    """
    aggregator = PredictiveAggregator(storage_file)
    return aggregator.build_advanced_forecast(symbol, url, percentage_shift)