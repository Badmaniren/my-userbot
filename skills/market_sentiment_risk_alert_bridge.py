from skills import market_sentiment_risk_hub
from skills import market_portfolio_alert_dispatcher

class MarketSentimentRiskAlertBridge:
    def __init__(self, token, chat_id, storage_file):
        self.token = token
        self.chat_id = chat_id
        self.storage_file = storage_file
        self.hub = market_sentiment_risk_hub.MarketSentimentRiskHub()

    def bridge_evaluate_and_dispatch(self, ticker, exchange, news_snippet, url, severity_level, min_threshold, channels):
        risk_data = self.hub.evaluate_risk(ticker, exchange, news_snippet)
        dispatch_result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=ticker,
            url=url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=channels
        )
        return {
            "risk_data": risk_data,
            "dispatch_result": dispatch_result
        }

    def bridge_process_stream(self, stream_source):
        stream_items = self.hub.process_stream(stream_source)
        results = []
        for item in stream_items:
            res = market_portfolio_alert_dispatcher.process_stream_alert(item)
            results.append(res)
        return results

def process_sentiment_risk_and_dispatch_alert(
    ticker,
    exchange,
    news_snippet,
    url,
    telegram_token,
    chat_id,
    storage_file,
    severity_level="MEDIUM",
    min_threshold=0.5,
    channels=None
):
    if channels is None:
        channels = ["telegram"]
        
    bridge = MarketSentimentRiskAlertBridge(
        token=telegram_token,
        chat_id=chat_id,
        storage_file=storage_file
    )
    
    result = bridge.bridge_evaluate_and_dispatch(
        ticker=ticker,
        exchange=exchange,
        news_snippet=news_snippet,
        url=url,
        severity_level=severity_level,
        min_threshold=min_threshold,
        channels=channels
    )
    
    return {
        "risk_evaluation": result["risk_data"],
        "dispatch_status": result["dispatch_result"]
    }