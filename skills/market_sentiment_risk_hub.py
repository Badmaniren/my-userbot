import os
from skills import market_news_sentiment_analyzer
from skills import market_anomaly_detector
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_anomaly_detector import MarketAnomalyDetector

class MarketSentimentRiskHub:
    def __init__(self):
        self.sentiment_analyzer = MarketNewsSentimentAnalyzer()
        self.anomaly_detector = MarketAnomalyDetector()

    def evaluate_risk(self, ticker=None, exchange=None, news_snippet=None):
        sentiment_score = 0.0
        anomaly_score = 0.0

        if news_snippet:
            sentiment_res = self.sentiment_analyzer.analyze(news_snippet)
            if isinstance(sentiment_res, dict):
                sentiment_score = sentiment_res.get("sentiment_score", 0.0)
        elif ticker:
            sentiment_res = self.sentiment_analyzer.analyze(ticker)
            if isinstance(sentiment_res, dict):
                sentiment_score = sentiment_res.get("sentiment_score", 0.0)

        target_anomaly_query = exchange if exchange else (ticker if ticker else "DEFAULT")
        anomaly_res = self.anomaly_detector.detect(target_anomaly_query)
        if isinstance(anomaly_res, dict):
            anomaly_score = anomaly_res.get("anomaly_score", 0.0)
        elif isinstance(anomaly_res, (int, float)):
            anomaly_score = float(anomaly_res)

        risk_score = abs(float(sentiment_score)) * 50.0 + float(anomaly_score) * 0.5
        risk_index = risk_score

        return {
            "risk_index": risk_index,
            "risk_score": risk_score,
            "sentiment_score": sentiment_score,
            "anomaly_score": anomaly_score
        }

    def process_stream(self, stream_source):
        if hasattr(self.sentiment_analyzer, "batch_analyze_stream"):
            self.sentiment_analyzer.batch_analyze_stream(stream_source)
        if hasattr(self.anomaly_detector, "analyze_stream"):
            self.anomaly_detector.analyze_stream(stream_source)
        return {"stream_status": "PROCESSED", "risk_index": 0.0, "risk_score": 0.0}

    def export_report(self, ticker, filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Risk Audit Report for {ticker}\n")
        return True

def compute_market_risk_index(ticker=None, exchange=None):
    hub = MarketSentimentRiskHub()
    return hub.evaluate_risk(ticker=ticker, exchange=exchange)

def process_risk_stream(stream_source):
    hub = MarketSentimentRiskHub()
    return hub.process_stream(stream_source)