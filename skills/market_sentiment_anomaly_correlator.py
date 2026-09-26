import uuid
from skills.market_anomaly_detector import MarketAnomalyDetector
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer

class MarketSentimentAnomalyException(Exception):
    """Custom exception for market sentiment anomaly correlation errors."""
    pass

class MarketSentimentAnomalyCorrelator:
    def __init__(self):
        self.anomaly_detector = MarketAnomalyDetector()
        self.news_analyzer = MarketNewsSentimentAnalyzer()

    def correlate(self, ticker, news_snippet):
        try:
            anomaly_result = self.anomaly_detector.detect(ticker)
            
            # Ensure news_snippet passed to analyzer is a string
            if isinstance(news_snippet, dict):
                news_text = news_snippet.get("text", news_snippet.get("content", str(news_snippet)))
            else:
                news_text = str(news_snippet)
                
            sentiment_result = self.news_analyzer.analyze(news_text)
            
            # Simple correlation index calculation based on anomaly score and sentiment
            anomaly_score = anomaly_result.get("anomaly_score", anomaly_result.get("score", 1.0)) if isinstance(anomaly_result, dict) else 1.0
            sentiment_score = sentiment_result.get("sentiment", sentiment_result.get("score", 0.0)) if isinstance(sentiment_result, dict) else 0.0
            correlation_index = round(float(anomaly_score) * abs(float(sentiment_score)), 4)

            return {
                "ticker": ticker,
                "anomaly": anomaly_result,
                "sentiment": sentiment_result,
                "correlation_index": correlation_index
            }
        except Exception as e:
            if isinstance(e, MarketSentimentAnomalyException):
                raise e
            raise MarketSentimentAnomalyException(str(e))

    def analyze_correlation_stream(self, stream_source):
        return []

    def process_audit_stream(self, filename):
        try:
            with open(filename, 'rb') as f:
                content = f.read()
            self.news_analyzer.process_and_store(content)
            return True
        except Exception as e:
            if isinstance(e, MarketSentimentAnomalyException):
                raise e
            raise MarketSentimentAnomalyException(str(e))


def correlate_anomaly_with_sentiment(exchange, news_snippet):
    detector = MarketAnomalyDetector()
    analyzer = MarketNewsSentimentAnalyzer()
    
    anomalies = detector.analyze_stream(exchange)
    sentiments = analyzer.batch_analyze_stream(news_snippet)
    
    return {
        "exchange": exchange,
        "matched_events": list(zip(anomalies, sentiments))
    }


def market_sentiment_anomaly_correlator(correlation_input):
    ticker = correlation_input.get("ticker")
    anomaly = correlation_input.get("anomaly")
    sentiment = correlation_input.get("sentiment")
    
    anomaly_score = anomaly.get("anomaly_score", anomaly.get("score", 1.0)) if anomaly else 1.0
    sentiment_score = sentiment.get("sentiment", sentiment.get("score", 0.0)) if sentiment else 0.0
    
    correlation_index = round(float(anomaly_score) * abs(float(sentiment_score)), 4)
    
    return {
        "correlation_id": uuid.uuid4().hex,
        "ticker": ticker,
        "status": "CORRELATED",
        "correlation_index": correlation_index,
        "anomaly": anomaly,
        "sentiment": sentiment
    }