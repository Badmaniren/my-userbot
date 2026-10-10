import os
from skills.market_portfolio_realtime_stream_analytics_hub import (
    MarketPortfolioRealtimeStreamAnalyticsHub,
    process_realtime_stream_hub
)
from skills.market_portfolio_realtime_stream_alert_sink import (
    market_portfolio_realtime_stream_alert_sink,
    process_stream_and_dispatch_alerts
)


class MarketPortfolioRealtimeStreamDashboardBridge:
    def __init__(self, storage=None, storage_file=None, stream_source=None):
        self.storage_file = storage_file if storage_file is not None else storage
        self.stream_source = stream_source
        self._analytics_hub = None

    @property
    def analytics_hub(self):
        if self._analytics_hub is not None:
            return self._analytics_hub
        return MarketPortfolioRealtimeStreamAnalyticsHub(
            storage_file=self.storage_file,
            stream_source=self.stream_source
        )

    @analytics_hub.setter
    def analytics_hub(self, value):
        self._analytics_hub = value

    def process_and_bridge(self, context=None, output_path=None):
        try:
            result = self.analytics_hub.process_stream(context)
        except Exception as e:
            result = {"status": "error", "message": str(e), "context": context}

        if isinstance(result, dict) and result.get("status") == "error":
            if isinstance(context, dict) and isinstance(context.get("metrics"), dict) and context.get("metrics"):
                return context["metrics"]
            return result

        if output_path and isinstance(context, dict) and isinstance(context.get("metrics"), dict):
            self.analytics_hub.audit_stream_data(context["metrics"], output_path)
        elif output_path and isinstance(context, dict):
            self.analytics_hub.audit_stream_data(context, output_path)
        return result if isinstance(result, dict) else {}

    def process_stream(self, context=None):
        try:
            res = self.analytics_hub.process_stream(context)
        except Exception as e:
            res = {"status": "error", "message": str(e), "context": context}

        if isinstance(res, dict) and res.get("status") == "error":
            if isinstance(context, dict) and context.get("metrics"):
                return context["metrics"]
            if isinstance(context, dict):
                return context
        return res if isinstance(res, dict) else {}

    def get_realtime_metrics(self, symbol):
        return self.analytics_hub.get_realtime_metrics(symbol)


def market_portfolio_realtime_stream_dashboard_bridge(
    storage_file=None,
    stream_source=None,
    output_path=None,
    symbol=None,
    url=None,
    token=None,
    chat_id=None,
    severity=None,
    threshold=None,
    channels=None,
    payload=None,
    context=None
):
    hub_instance = MarketPortfolioRealtimeStreamAnalyticsHub(
        storage_file=storage_file,
        stream_source=stream_source
    )
    
    if context is None:
        context = {}
        
    analytics_result = hub_instance.process_stream(context)
    
    sink_result = market_portfolio_realtime_stream_alert_sink(
        payload=payload,
        output_path=output_path,
        storage=storage_file,
        url=url,
        token=token,
        chat_id=chat_id,
        severity=severity,
        threshold=threshold,
        channels=channels,
        symbol=symbol
    )
    
    return {
        "analytics": analytics_result,
        "alert_sink": sink_result
    }


def process_dashboard_stream_bridge(
    output_path=None,
    storage_file=None,
    symbol=None,
    url=None,
    token=None,
    chat_id=None,
    severity=None,
    threshold=None,
    channels=None
):
    hub_instance = MarketPortfolioRealtimeStreamAnalyticsHub(
        storage_file=storage_file,
        stream_source=None
    )
    metrics = hub_instance.get_realtime_metrics(symbol)
    
    return {
        "metrics": metrics
    }


def process_dashboard_bridge_stream(
    storage=None,
    stream_source=None,
    payload=None,
    output_path=None,
    symbol=None,
    url=None,
    token=None,
    chat_id=None,
    severity=None,
    threshold=None,
    channels=None
):
    hub_instance = MarketPortfolioRealtimeStreamAnalyticsHub(
        storage_file=storage,
        stream_source=stream_source
    )
    if payload and output_path:
        hub_instance.audit_stream_data(payload, output_path)
    
    metrics = hub_instance.get_realtime_metrics(symbol)

    return metrics if isinstance(metrics, dict) else {"status": "ok"}