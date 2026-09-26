import io
import uuid

from skills.db_storage import db_storage
from skills.market_anomaly_detector import market_anomaly_detector
from skills.market_news_sentiment_analyzer import market_news_sentiment_analyzer
from skills.market_portfolio_data_exporter import export as market_portfolio_data_exporter


class MarketSentimentRiskMatrix:
    def __init__(self):
        pass

    def _compute_drawdown_prob(self, sentiment_score: float, anomaly_factor: float) -> float:
        # sentiment_score nominally in range [-1.0, 1.0]; negative sentiment -> higher drawdown probability
        sentiment_risk = (1.0 - max(-1.0, min(1.0, float(sentiment_score)))) / 2.0

        # anomaly_factor >= 0; higher anomaly -> higher drawdown probability
        anomaly_risk = max(0.0, min(1.0, float(anomaly_factor) / 10.0))

        prob = 0.5 * sentiment_risk + 0.5 * anomaly_risk
        return max(0.0, min(1.0, float(prob)))

    def calculate_matrix(self, portfolio_id: str) -> dict:
        sentiment_res = market_news_sentiment_analyzer.analyze(portfolio_id)
        if isinstance(sentiment_res, dict):
            sentiment_score = float(sentiment_res.get("score", sentiment_res.get("sentiment_score", 0.0)))
        else:
            sentiment_score = float(sentiment_res)

        anomaly_res = market_anomaly_detector.detect(portfolio_id)
        if isinstance(anomaly_res, dict):
            anomaly_factor = float(anomaly_res.get("anomaly_factor", anomaly_res.get("threshold", anomaly_res.get("anomaly_score", 0.0))))
        else:
            anomaly_factor = float(anomaly_res)

        drawdown_prob = self._compute_drawdown_prob(sentiment_score, anomaly_factor)

        return {
            "portfolio_id": portfolio_id,
            "sentiment_score": sentiment_score,
            "anomaly_factor": anomaly_factor,
            "drawdown_probability": drawdown_prob
        }

    def evaluate_from_stream(self, portfolio_id: str) -> dict:
        stream = db_storage.fetch_stream(portfolio_id)
        if hasattr(stream, "read"):
            content = stream.read()
        elif isinstance(stream, (bytes, bytearray)):
            content = stream
        else:
            content = b""

        return {
            "portfolio_id": portfolio_id,
            "processed": True,
            "stream_len": len(content)
        }

    def export_matrix(self, target: str, data: dict = None) -> bool:
        if hasattr(market_portfolio_data_exporter, "export"):
            if data is not None:
                res = market_portfolio_data_exporter.export(target, data)
            else:
                res = market_portfolio_data_exporter.export(target)
            return bool(res) if res is not None else True
        return True


def market_sentiment_risk_matrix(portfolio_id: str, sentiment_input=None, anomaly_input=None, **kwargs) -> dict:
    risk_matrix_id = str(uuid.uuid4())

    if isinstance(sentiment_input, dict):
        sentiment_score = float(sentiment_input.get("score", sentiment_input.get("sentiment_score", 0.0)))
    elif sentiment_input is not None:
        sentiment_score = float(sentiment_input)
    else:
        sentiment_score = 0.0

    if isinstance(anomaly_input, dict):
        anomaly_factor = float(anomaly_input.get("threshold", anomaly_input.get("anomaly_factor", anomaly_input.get("anomaly_score", 0.0))))
    elif anomaly_input is not None:
        anomaly_factor = float(anomaly_input)
    else:
        anomaly_factor = 0.0

    calculator = MarketSentimentRiskMatrix()
    drawdown_probability = calculator._compute_drawdown_prob(sentiment_score, anomaly_factor)

    record = {
        "risk_matrix_id": risk_matrix_id,
        "portfolio_id": portfolio_id,
        "sentiment_score": sentiment_score,
        "anomaly_factor": anomaly_factor,
        "drawdown_probability": drawdown_probability
    }

    if callable(db_storage):
        db_storage(action="save", record_id=risk_matrix_id, record=record)
    elif hasattr(db_storage, "save_record"):
        db_storage.save_record(risk_matrix_id, record)

    return record
