from skills import market_portfolio_realtime_stream_ingestor
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics


class MarketPortfolioRealtimeStreamAnalyticsHub:
    def __init__(self, storage_file: str, stream_source: str):
        self.storage_file = storage_file
        self.stream_source = stream_source
        self.analytics_engine = PortfolioPerformanceAnalytics(self.storage_file)

    def process_stream(self, context: dict) -> dict:
        try:
            return market_portfolio_realtime_stream_ingestor.start_new(context, self.stream_source)
        except Exception as e:
            return {"status": "error", "message": str(e), "context": context}

    def audit_stream_data(self, payload: dict, output_path: str) -> dict:
        return market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor(payload, output_path)

    def get_realtime_metrics(self, symbol: str) -> dict:
        self.analytics_engine.load_data(self.storage_file)
        return self.analytics_engine.calculate_metrics(symbol)

    def evaluate_stream_performance(self, symbol: str) -> dict:
        self.analytics_engine.load_data(self.storage_file)
        return self.analytics_engine.evaluate_performance(symbol)


def process_realtime_stream_hub(output_path: str, storage_file: str, symbol: str) -> dict:
    analytics = PortfolioPerformanceAnalytics(storage_file)
    try:
        analytics.load_data(storage_file)
        metrics = analytics.calculate_metrics(symbol)
    except Exception:
        metrics = {"symbol": symbol, "status": "initialized"}

    return {
        "output_path": output_path,
        "storage_file": storage_file,
        "metrics": metrics
    }