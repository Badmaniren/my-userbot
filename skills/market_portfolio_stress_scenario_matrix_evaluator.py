import requests
import bs4

class MarketPortfolioStressScenarioMatrixEvaluator:
    def __init__(self, db_storage, extractor_tool_1790087207, extractor_tool_1790102839=None, extractor_tool_102839=None):
        self.db_storage = db_storage
        self.extractor_tool_1790087207 = extractor_tool_1790087207
        self.extractor_tool_1790102839 = extractor_tool_1790102839 if extractor_tool_1790102839 is not None else extractor_tool_102839

    def evaluate_matrix(self, portfolio_id: str, historical_window: int) -> dict:
        history = self.db_storage.fetch_history(portfolio_id, historical_window)
        
        response = requests.get("https://example.com/api/stress-matrix")
        
        values = [item.get("value", 0.0) for item in history] if history else [0.0]
        avg_value = sum(values) / len(values) if values else 0.0
        evaluation_score = round(min(max(avg_value / 1000.0, 0.0), 1.0), 4)

        return {
            "portfolio_id": portfolio_id,
            "evaluation_score": evaluation_score,
            "payload_data": response.content.decode('utf-8', errors='ignore')
        }

    def evaluate_stream_matrix(self, portfolio_id: str, stream_mock) -> dict:
        stream = self.db_storage.fetch_stream(portfolio_id)
        content = stream.read()
        
        soup = bs4.BeautifulSoup(content, 'html.parser')
        _ = soup.text

        return {
            "portfolio_id": portfolio_id,
            "fallback_triggered": True
        }

    def detect_matrix_anomalies(self, scenario_token: str, threshold: float) -> bool:
        analysis_result = self.extractor_tool_1790087207.analyze(scenario_token)
        anomaly_metric = analysis_result.get("anomaly_metric", 0.0)
        return anomaly_metric > threshold


def evaluate_stress_scenario_matrix(evaluation_payload: dict) -> dict:
    portfolio_id = evaluation_payload.get("portfolio_id")
    evaluation_id = evaluation_payload.get("evaluation_id")
    monte_carlo = evaluation_payload.get("monte_carlo_metrics", {})
    
    if "score" in monte_carlo:
        base_val = monte_carlo.get("score", 0.5)
        matrix_score = round(float(base_val) * 1.1, 4) if isinstance(base_val, (int, float)) else 0.85
    else:
        matrix_score = 0.85
    
    return {
        "evaluation_id": evaluation_id,
        "portfolio_id": portfolio_id,
        "matrix_score": matrix_score
    }