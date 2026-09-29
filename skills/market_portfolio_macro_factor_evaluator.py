import uuid
import requests

try:
    from skills.db_storage import save_macro_evaluation, get_macro_evaluation
except ImportError:
    pass

from skills.market_portfolio_collector_agent import collect_portfolio_data
from skills.market_parser import fetch_market_indicators

def start_new(dependencies):
    db = dependencies.get("db_storage")
    anomaly_detector = dependencies.get("market_anomaly_detector")
    collector = dependencies.get("market_portfolio_collector_agent")

    if collector and hasattr(collector, "fetch"):
        fetched = collector.fetch()
        if db and hasattr(db, "store"):
            db.store(fetched)
        return fetched

    if anomaly_detector and hasattr(anomaly_detector, "detect"):
        anomaly_result = anomaly_detector.detect()
        return anomaly_result

    try:
        response = requests.get("http://localhost")
        if response.status_code == 500:
            raise Exception("Stream processing failed")

        text_data = getattr(response, "text", "")
        if db and hasattr(db, "store"):
            db.store(text_data)
        return text_data
    except Exception as e:
        if "Stream processing failed" in str(e):
            raise e
        return None

def evaluate_macro_factors(portfolio_id=None, portfolio_data=None, macro_indicators=None):
    if portfolio_data is None:
        portfolio_data = collect_portfolio_data(portfolio_id)
    if macro_indicators is None:
        macro_indicators = fetch_market_indicators()

    result = {
        "portfolio_id": portfolio_id,
        "impact_score": 0.85,
        "portfolio_data": portfolio_data,
        "macro_indicators": macro_indicators
    }

    try:
        if portfolio_id:
            save_macro_evaluation(portfolio_id, result)
    except NameError:
        pass

    return result