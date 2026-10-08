import os
import json
from skills import db_storage as default_db_storage
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_portfolio_stress_scenario_matrix_evaluator import MarketPortfolioStressScenarioMatrixEvaluator

class MarketPortfolioSentimentStressCorrelator:
    def __init__(self, db_storage=None, extractor_tool_1790087207=None):
        if db_storage is None:
            db_storage = default_db_storage
        self.sentiment_analyzer = MarketNewsSentimentAnalyzer()
        try:
            self.stress_evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
                db_storage=db_storage,
                extractor_tool_1790087207=extractor_tool_1790087207
            )
        except TypeError:
            try:
                self.stress_evaluator = MarketPortfolioStressScenarioMatrixEvaluator()
            except TypeError:
                self.stress_evaluator = MarketPortfolioStressScenarioMatrixEvaluator(db_storage, extractor_tool_1790087207)

    def correlate(self, portfolio_id: str, news_text: str, window: int) -> dict:
        sentiment_data = self.sentiment_analyzer.analyze(news_text)

        try:
            stress_data = self.stress_evaluator.evaluate_matrix(portfolio_id, window)
        except TypeError:
            stress_data = self.stress_evaluator.evaluate_matrix(portfolio_id=portfolio_id, historical_window=window)

        score = sentiment_data.get("sentiment_score", 0.0) if sentiment_data else 0.0
        drawdown = stress_data.get("max_drawdown", stress_data.get("drawdown", 0.0))

        correlation_coefficient = float(score * (drawdown / 100.0) if drawdown != 0 else 0.0)
        panic_sensitivity_index = float(abs(score * drawdown))

        return {
            "portfolio_id": portfolio_id,
            "correlation_coefficient": correlation_coefficient,
            "panic_sensitivity_index": panic_sensitivity_index,
            "sentiment_data": sentiment_data,
            "stress_data": stress_data
        }

    def correlate_stream(self, portfolio_id: str, filename: str, stream_bytes) -> dict:
        batch_results = self.sentiment_analyzer.batch_analyze_stream(filename)
        stream_matrix = self.stress_evaluator.evaluate_stream_matrix(portfolio_id, stream_bytes)

        return {
            "portfolio_id": portfolio_id,
            "aggregated_sentiment": batch_results,
            "stream_stress_matrix": stream_matrix
        }

    def detect_panic_anomalies(self, token: str, threshold: float) -> bool:
        return self.stress_evaluator.detect_matrix_anomalies(token, threshold)

def correlate_sentiment_with_stress(payload: dict) -> dict:
    portfolio_id = payload.get("portfolio_id")
    sentiment_data = payload.get("sentiment_data", {})
    stress_matrix = payload.get("stress_matrix", {})
    correlation_factor = payload.get("correlation_factor", 1.0)

    score = sentiment_data.get("sentiment_score", 0.0)
    drawdown = stress_matrix.get("max_drawdown", stress_matrix.get("drawdown", 0.0))

    sensitivity_index = float(abs(score * drawdown) * correlation_factor)

    result = {
        "portfolio_id": portfolio_id,
        "sensitivity_index": sensitivity_index,
        "sentiment_data": sentiment_data,
        "stress_matrix": stress_matrix
    }

    os.makedirs("reports", exist_ok=True)
    output_path = f"reports/sentiment_stress_{portfolio_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    return result