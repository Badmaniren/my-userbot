import uuid
import io

try:
    from skills.db_storage import db_storage
except ImportError:
    db_storage = None

try:
    from skills.market_anomaly_detector import market_anomaly_detector
except ImportError:
    market_anomaly_detector = None

try:
    from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
except ImportError:
    market_portfolio_alert_dispatcher = None

try:
    from skills.market_portfolio_stress_audit_exporter_v2 import market_portfolio_stress_audit_exporter_v2
except ImportError:
    market_portfolio_stress_audit_exporter_v2 = None


def start_new(portfolio_id: str, audit_id: str, threshold: float) -> dict:
    if market_portfolio_stress_audit_exporter_v2 and hasattr(market_portfolio_stress_audit_exporter_v2, 'export_stream'):
        market_portfolio_stress_audit_exporter_v2.export_stream(portfolio_id=portfolio_id, audit_id=audit_id)

    evaluation = {}
    if market_anomaly_detector and hasattr(market_anomaly_detector, 'evaluate'):
        evaluation = market_anomaly_detector.evaluate(
            portfolio_id=portfolio_id,
            audit_id=audit_id,
            threshold=threshold
        )

    is_anomaly = evaluation.get("is_anomaly", False)
    score = evaluation.get("score", 0.0)
    metric = evaluation.get("metric", "")

    if is_anomaly and market_portfolio_alert_dispatcher and hasattr(market_portfolio_alert_dispatcher, 'dispatch'):
        market_portfolio_alert_dispatcher.dispatch(
            portfolio_id=portfolio_id,
            audit_id=audit_id,
            score=score,
            metric=metric
        )

    return {
        "anomaly_detected": is_anomaly,
        "score": score,
        "metric": metric
    }


def market_portfolio_stress_audit_anomaly_sentinel(payload: dict) -> dict:
    portfolio_id = payload.get("portfolio_id")
    stress_audit_id = payload.get("stress_audit_id")
    audit_data = payload.get("audit_data", {})

    threshold = audit_data.get("threshold", 0.1)

    eval_result = {}
    if market_anomaly_detector and hasattr(market_anomaly_detector, 'evaluate'):
        eval_result = market_anomaly_detector.evaluate(
            portfolio_id=portfolio_id,
            audit_id=stress_audit_id,
            threshold=threshold
        )

    is_anomaly = eval_result.get("is_anomaly", True)
    score = eval_result.get("score", 5.0)
    sentinel_event_id = f"sentinel_{uuid.uuid4().hex}"

    result_data = {
        "sentinel_event_id": sentinel_event_id,
        "portfolio_id": portfolio_id,
        "stress_audit_id": stress_audit_id,
        "anomaly_detected": is_anomaly,
        "score": score
    }

    if db_storage:
        db_storage({
            "action": "set",
            "key": sentinel_event_id,
            "value": result_data
        })

    return result_data
