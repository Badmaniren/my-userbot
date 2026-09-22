from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_portfolio_visualizer_v2 import PortfolioVisualizer


class MarketPortfolioRiskDashboard:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.analytics = PortfolioPerformanceAnalytics(storage_file)
        self.visualizer = PortfolioVisualizer(storage_file)

    def generate_dashboard(self, symbol: str):
        if hasattr(self.analytics, "load_data"):
            try:
                self.analytics.load_data(self.storage_file)
            except TypeError:
                self.analytics.load_data()

        if hasattr(self.visualizer, "load_data"):
            try:
                self.visualizer.load_data(self.storage_file)
            except TypeError:
                self.visualizer.load_data()

        metrics = self.analytics.calculate_metrics(symbol)
        performance = self.analytics.evaluate_performance(symbol)

        if hasattr(self.visualizer, "generate_ascii_chart"):
            ascii_chart = self.visualizer.generate_ascii_chart(symbol)
        elif hasattr(self.visualizer, "build_text_report"):
            ascii_chart = self.visualizer.build_text_report(symbol)
        else:
            ascii_chart = ""

        if not metrics and not performance and not ascii_chart:
            return {}

        dashboard_repr = f"Dashboard for {symbol}\nMetrics: {metrics}\nPerformance: {performance}\nChart:\n{ascii_chart}"
        return dashboard_repr


def generate_risk_dashboard(storage_file: str, symbol: str):
    instance = MarketPortfolioRiskDashboard(storage_file)
    return instance.generate_dashboard(symbol)