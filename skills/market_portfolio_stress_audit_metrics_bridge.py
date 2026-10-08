from skills import db_storage


def start_new(session_id, metric_name, value):
    conn = db_storage.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO market_portfolio_stress_audit_metrics_bridge (session_id, metric_name, value) VALUES (?, ?, ?)",
        (session_id, metric_name, value)
    )
    if hasattr(conn, "commit"):
        conn.commit()
    return session_id


def process_stress_audit_metrics_bridge(input_payload):
    if not isinstance(input_payload, dict):
        raise TypeError("Payload must be a dictionary")

    portfolio_id = input_payload.get("portfolio_id")
    audit_id = input_payload.get("audit_id")
    stress_metric = input_payload.get("stress_metric")
    timestamp = input_payload.get("timestamp")

    if not portfolio_id or not audit_id:
        raise KeyError("Missing portfolio_id or audit_id")

    if not isinstance(stress_metric, (int, float)):
        raise ValueError("stress_metric must be numeric")

    db = db_storage.DatabaseStorage()
    db.save_record("stress_audit_metrics", audit_id, {
        "portfolio_id": portfolio_id,
        "audit_id": audit_id,
        "stress_metric": stress_metric,
        "timestamp": timestamp
    })

    return {
        "status": "success",
        "audit_id": audit_id,
        "portfolio_id": portfolio_id,
        "processed_metric": stress_metric
    }
