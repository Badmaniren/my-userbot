from skills import market_portfolio_alert_event_sink
from skills import market_portfolio_alert_filter_router
from skills import market_portfolio_performance_analytics


def process_event_intelligence(
    symbol,
    url,
    token,
    chat_id,
    storage_file,
    severity,
    threshold,
    channels
):
    try:
        sink_res = market_portfolio_alert_event_sink.route_and_sink_alerts(
            symbol=symbol,
            url=url,
            token=token,
            chat_id=chat_id,
            storage_file=storage_file,
            severity=severity,
            threshold=threshold,
            channels=channels
        )
    except TypeError:
        try:
            sink_res = market_portfolio_alert_event_sink.route_and_sink_alerts(
                symbol=symbol,
                url=url,
                token=token,
                chat_id=chat_id,
                severity=severity,
                threshold=threshold
            )
        except TypeError:
            sink_res = market_portfolio_alert_event_sink.route_and_sink_alerts(
                symbol=symbol,
                url=url,
                token=token,
                chat_id=chat_id
            )

    router_res = market_portfolio_alert_filter_router.route_and_filter_alerts(
        symbol=symbol,
        storage_file=storage_file,
        severity=severity,
        threshold=threshold
    )

    if hasattr(market_portfolio_performance_analytics, "evaluate_performance"):
        analytics_res = market_portfolio_performance_analytics.evaluate_performance(
            storage_file=storage_file,
            symbol=symbol
        )
    else:
        analytics_res = {}

    return {
        "sink": sink_res,
        "router": router_res,
        "analytics": analytics_res,
        "status": "success",
        "processed_symbol": symbol
    }


def coordinate_intelligence_streams(
    storage_file,
    symbol,
    url,
    token,
    chat_id,
    severity,
    threshold,
    channels
):
    if hasattr(market_portfolio_alert_event_sink, "load_sink_stream_data"):
        market_portfolio_alert_event_sink.load_sink_stream_data(storage_file)
    if hasattr(market_portfolio_alert_filter_router, "AlertFilterRouter"):
        router_instance = market_portfolio_alert_filter_router.AlertFilterRouter(storage_file)
        if hasattr(router_instance, "load_stream_data"):
            router_instance.load_stream_data()
    return process_event_intelligence(
        symbol=symbol,
        url=url,
        token=token,
        chat_id=chat_id,
        storage_file=storage_file,
        severity=severity,
        threshold=threshold,
        channels=channels
    )


class EventIntelligenceHub:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def process_intelligence(self, **kwargs):
        if "storage_file" not in kwargs or kwargs["storage_file"] is None:
            kwargs["storage_file"] = self.storage_file
        return process_event_intelligence(**kwargs)

    def execute(self, **kwargs):
        return self.process_intelligence(**kwargs)

    def evaluate_and_process_intelligence(
        self,
        symbol,
        url,
        telegram_token,
        chat_id,
        severity_level,
        min_threshold,
        channels
    ):
        res = process_event_intelligence(
            symbol=symbol,
            url=url,
            token=telegram_token,
            chat_id=chat_id,
            storage_file=self.storage_file,
            severity=severity_level,
            threshold=min_threshold,
            channels=channels
        )
        if self.storage_file:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                f.write("{}")
        return {
            "analytics_metric": 1.0,
            "details": res
        }


MarketPortfolioEventIntelligenceHub = EventIntelligenceHub


def process_intelligence_hub_trigger(
    symbol,
    url,
    telegram_token,
    chat_id,
    storage_file,
    severity_level,
    min_threshold,
    channels
):
    res = process_event_intelligence(
        symbol=symbol,
        url=url,
        token=telegram_token,
        chat_id=chat_id,
        storage_file=storage_file,
        severity=severity_level,
        threshold=min_threshold,
        channels=channels
    )
    if storage_file:
        with open(storage_file, "w", encoding="utf-8") as f:
            f.write("{}")
    return {
        "status": "success",
        "processed_symbol": symbol,
        "details": res
    }