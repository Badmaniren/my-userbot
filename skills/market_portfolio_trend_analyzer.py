from skills import market_portfolio_monitor
from skills import market_portfolio_valuation


class PortfolioTrendAnalyzer:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self._monitor = None
        self._valuation = None

    @property
    def monitor(self):
        if self._monitor is None:
            self._monitor = market_portfolio_monitor.MarketReportGenerator(self.storage_file)
        return self._monitor

    @property
    def valuation(self):
        if self._valuation is None:
            self._valuation = market_portfolio_valuation.PortfolioValuation(self.storage_file)
        return self._valuation

    def analyze_trends(self, symbol: str, url: str) -> dict:
        report = self.monitor.generate_symbol_report(symbol)
        pnl = self.valuation.calculate_portfolio_pnl(url)
        summary = self.valuation.get_total_summary()
        valuation = summary.get("total_valuation") if summary else 0.0

        result = dict(report) if isinstance(report, dict) else {"report": report}
        result["symbol"] = symbol
        result["pnl"] = pnl
        result["valuation"] = valuation
        return result

    def analyze(self, symbol: str, url: str) -> dict:
        report = self.monitor.generate_symbol_report(symbol)
        self.valuation.evaluate_portfolio(url)
        return {
            "trend": report,
            "symbol": symbol
        }


def analyze_portfolio_trends(storage_file: str, symbol: str, url: str) -> dict:
    monitor = market_portfolio_monitor.MarketReportGenerator(storage_file)
    valuation = market_portfolio_valuation.PortfolioValuation(storage_file)

    report = monitor.generate_symbol_report(symbol)
    valuation.evaluate_portfolio(url)

    return {
        "report": report,
        "symbol": symbol
    }


def analyze_trend(storage_file: str, symbol: str, url: str) -> dict:
    analyzer = PortfolioTrendAnalyzer(storage_file)
    return analyzer.analyze(symbol, url)
