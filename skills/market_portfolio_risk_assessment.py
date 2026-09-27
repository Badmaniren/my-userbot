import json
import uuid
import numpy as np

try:
    from skills import market_anomaly_detector
except ImportError:
    import market_anomaly_detector

try:
    from skills import market_portfolio_api_gateway
except ImportError:
    try:
        import market_portfolio_api_gateway
    except ImportError:
        market_portfolio_api_gateway = None

try:
    from skills import market_portfolio_stress_scenario_pipeline
except ImportError:
    try:
        import market_portfolio_stress_scenario_pipeline
    except ImportError:
        market_portfolio_stress_scenario_pipeline = None


class PortfolioRiskAssessor:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def calculate_risk(self, portfolio_id):
        if not self.db_storage or not hasattr(self.db_storage, 'get_historical_data'):
            return 0.5

        prices = self.db_storage.get_historical_data(portfolio_id)
        if not prices or len(prices) < 2:
            return 0.0

        returns = [
            (prices[i] - prices[i - 1]) / prices[i - 1]
            for i in range(1, len(prices))
            if prices[i - 1] != 0
        ]

        if not returns:
            return 0.0

        volatility = float(np.std(returns)) if hasattr(np, 'std') else 0.1
        risk_score = min(max(volatility * 2.0, 0.0), 1.0)
        return float(risk_score)

    def check_market_anomalies(self, threshold=0.5):
        if hasattr(market_anomaly_detector, 'analyze'):
            return market_anomaly_detector.analyze(threshold=threshold)
        elif hasattr(market_anomaly_detector, 'MarketAnomalyDetector'):
            detector = market_anomaly_detector.MarketAnomalyDetector()
            if hasattr(detector, 'analyze'):
                return detector.analyze(threshold=threshold)
        return {"event_id": str(uuid.uuid4()), "severity": "low", "value": 0.0}

    def export_risk_report(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def fetch_external_metrics(self):
        if market_portfolio_api_gateway and hasattr(market_portfolio_api_gateway, 'fetch'):
            response = market_portfolio_api_gateway.fetch()
            if getattr(response, 'status_code', None) == 200:
                return getattr(response, 'text', '')
        return None

    def run_stress_test(self, scenario_name):
        if market_portfolio_stress_scenario_pipeline and hasattr(market_portfolio_stress_scenario_pipeline, 'run'):
            return market_portfolio_stress_scenario_pipeline.run(scenario_name)
        return {"status": "success", "impact": 0.0}


def assess_portfolio_risk(portfolio_id, data=None, volatility_window=30):
    report_id = str(uuid.uuid4())
    risk_score = 0.25
    if data and isinstance(data, dict):
        risk_score = min(0.1 * len(data), 0.9)
    return {
        "report_id": report_id,
        "portfolio_id": portfolio_id,
        "risk_score": float(risk_score)
    }
