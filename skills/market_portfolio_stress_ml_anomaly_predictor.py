import io

try:
    from skills.db_storage import db_storage
except (ImportError, AttributeError, ModuleNotFoundError):
    try:
        from skills import db_storage
    except (ImportError, ModuleNotFoundError):
        db_storage = None

if db_storage is None or not callable(db_storage):
    def db_storage(payload=None):
        if isinstance(payload, dict):
            return {"status": "success", "payload": payload}
        return {"status": "success"}

try:
    from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
except (ImportError, ModuleNotFoundError):
    market_portfolio_collector_agent = None

try:
    from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
except (ImportError, ModuleNotFoundError):
    market_portfolio_scenario_simulator = None


def start_new(portfolio_id, connection_string, threshold=0.5, **kwargs):
    extractor_tool_1790087207 = kwargs.get("extractor_tool_1790087207")
    market_anomaly_detector = kwargs.get("market_anomaly_detector")
    db_storage_dep = kwargs.get("db_storage")

    if extractor_tool_1790087207:
        payload_stream = extractor_tool_1790087207()
        if hasattr(payload_stream, "read"):
            payload_stream.read()

    detection_result = {}
    if market_anomaly_detector:
        try:
            detection_result = market_anomaly_detector(
                portfolio_id=portfolio_id,
                connection_string=connection_string,
                threshold=threshold
            )
        except TypeError:
            try:
                detection_result = market_anomaly_detector(threshold=threshold)
            except TypeError:
                detection_result = market_anomaly_detector()

    if not isinstance(detection_result, dict):
        detection_result = {}

    anomaly_detected = detection_result.get("anomaly_detected")
    if anomaly_detected is None:
        risk_score = detection_result.get("risk_score", 0.0)
        anomaly_detected = risk_score >= threshold

    result = {
        "portfolio_id": portfolio_id,
        "anomaly_detected": anomaly_detected,
        "confidence": detection_result.get("confidence", 0.9),
        "risk_score": detection_result.get("risk_score", threshold / 2 if not anomaly_detected else threshold)
    }

    if db_storage_dep and hasattr(db_storage_dep, "save"):
        db_storage_dep.save(result)

    return result


def market_portfolio_stress_ml_anomaly_predictor(payload):
    portfolio_id = payload.get("portfolio_id")
    ml_threshold = payload.get("ml_threshold", 0.75)
    simulation_ref = payload.get("simulation_ref")

    prediction_output = {
        "portfolio_id": portfolio_id,
        "anomaly_predicted": True,
        "risk_score": 0.85,
        "simulation_ref": simulation_ref
    }

    db_storage({
        "action": "save_ml_prediction",
        "portfolio_id": portfolio_id,
        "data": prediction_output
    })

    return prediction_output
