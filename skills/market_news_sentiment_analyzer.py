import re
import io

try:
    from skills import db_storage
except ImportError:
    db_storage = None


class MarketNewsSentimentAnalyzer:
    def __init__(self):
        self.bullish_keywords = [
            "profit", "surge", "growth", "gain", "breakout", 
            "upward", "rally", "momentum", "bullish", "earnings", "extraordinary"
        ]
        self.bearish_keywords = [
            "drop", "crash", "loss", "liquidation", "panic", "bearish", "suffer"
        ]

    def analyze(self, raw_news: str) -> dict:
        text_lower = raw_news.lower()
        
        bullish_count = sum(1 for kw in self.bullish_keywords if kw in text_lower)
        bearish_count = sum(1 for kw in self.bearish_keywords if kw in text_lower)
        
        score = float(bullish_count - bearish_count)
        
        if score > 0:
            sentiment = "bullish"
        elif score < 0:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
            
        identifier = None
        match = re.search(r"\[([a-f0-9\-]{32,})\]", raw_news)
        if match:
            identifier = match.group(1)
        else:
            match_id = re.search(r"ID-([a-f0-9\-]{36})", raw_news)
            if match_id:
                identifier = match_id.group(1)

        result = {
            "sentiment": sentiment,
            "score": score
        }
        if identifier:
            result["identifier"] = identifier
            
        return result

    def batch_analyze_stream(self, filename: str) -> list:
        results = []
        with open(filename, 'rb') as f:
            content = f.read()
        stream = io.BytesIO(content)
        for line in stream:
            decoded = line.decode('utf-8').strip()
            if decoded:
                results.append(self.analyze(decoded))
        return results

    def extract_entities(self, text: str) -> list:
        tickers = re.findall(r"\$([A-Z]+)", text)
        return tickers

    def process_and_store(self, news_item: str) -> bool:
        analysis = self.analyze(news_item)
        if db_storage is not None and hasattr(db_storage, 'save_sentiment_record'):
            return db_storage.save_sentiment_record(analysis)
        return True


def analyze_news_sentiment(parsed_data) -> dict:
    analyzer = MarketNewsSentimentAnalyzer()
    if isinstance(parsed_data, dict):
        text = parsed_data.get("raw_text", "")
        if not text:
            text = " ".join(str(v) for v in parsed_data.values())
        res = analyzer.analyze(text)
        if "identifier" not in res and "identifier" in parsed_data:
            res["identifier"] = parsed_data["identifier"]
        return res
    elif isinstance(parsed_data, str):
        return analyzer.analyze(parsed_data)
    return {"sentiment": "neutral", "score": 0.0}


def parse_market_news(raw_news_snippet: str) -> dict:
    match_uuid = re.search(r"ID-([a-f0-9\-]{36}):", raw_news_snippet)
    identifier = match_uuid.group(1) if match_uuid else None
    return {
        "identifier": identifier,
        "raw_text": raw_news_snippet
    }