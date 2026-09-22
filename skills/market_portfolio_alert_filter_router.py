import sys
import json
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics


class AlertFilterRouter:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.analytics = PortfolioPerformanceAnalytics(storage_file)

    def process_and_route(
        self,
        symbol: str,
        url: str,
        telegram_token: str,
        chat_id: str,
        severity_level: str,
        min_threshold: float,
        channels: list
    ):
        analytics_data = self.analytics.evaluate_performance(symbol)
        
        # Фильтрация по статусу / приоритету
        if severity_level == "LOW" and analytics_data.get("status") == "FAIL":
            return {
                "dispatched": False,
                "analytics_data": analytics_data
            }

        dispatch_result = dispatch_portfolio_alerts(
            symbol=symbol,
            url=url,
            telegram_token=telegram_token,
            chat_id=chat_id,
            storage_file=self.storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=channels
        )

        return {
            "dispatch_result": dispatch_result,
            "analytics_data": analytics_data,
            "status": analytics_data.get("status", "PASS")
        }

    def load_stream_data(self):
        if hasattr(self.analytics, "load_data"):
            return self.analytics.load_data()
        with open(self.storage_file, "rb") as f:
            return f.read()

    def route_filtered_alerts(
        self,
        symbol: str,
        url: str,
        telegram_token: str,
        chat_id: str,
        severity_level: str,
        min_threshold: float,
        channels: list
    ):
        return self.process_and_route(
            symbol=symbol,
            url=url,
            telegram_token=telegram_token,
            chat_id=chat_id,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=channels
        )


def route_and_filter_alerts(
    storage_file: str,
    symbol: str,
    url: str,
    telegram_token: str,
    chat_id: str,
    severity_level: str,
    min_threshold: float,
    channels: list
):
    router = AlertFilterRouter(storage_file)
    return router.process_and_route(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        severity_level=severity_level,
        min_threshold=min_threshold,
        channels=channels
    )


def filter_and_route_portfolio_alerts(
    symbol: str,
    url: str,
    telegram_token: str,
    chat_id: str,
    storage_file: str,
    severity_level: str,
    min_threshold: float,
    channels: list
):
    router = AlertFilterRouter(storage_file)
    return router.process_and_route(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        severity_level=severity_level,
        min_threshold=min_threshold,
        channels=channels
    )


def process_alert_filter_routing(
    symbol: str,
    url: str,
    telegram_token: str,
    chat_id: str,
    storage_file: str,
    severity_level: str,
    min_threshold: float,
    channels: list
):
    router = AlertFilterRouter(storage_file)
    return router.process_and_route(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        severity_level=severity_level,
        min_threshold=min_threshold,
        channels=channels
    )