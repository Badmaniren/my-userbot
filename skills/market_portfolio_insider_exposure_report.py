import uuid
import random
import os
import json

from skills.db_storage import save_report_state, get_report_state
from skills.market_insider_activity_tracker import track_insider_activity
from skills.market_anomaly_detector import detect_market_anomalies


def generate_insider_exposure_report(*args, **kwargs):
    db = kwargs.get('db_storage') or (args[0] if len(args) > 0 else None)
    tracker = kwargs.get('market_insider_activity_tracker') or (args[1] if len(args) > 1 else None)
    detector = kwargs.get('market_anomaly_detector') or (args[2] if len(args) > 2 else None)

    if db and hasattr(db, 'fetch_data'):
        db.fetch_data()
    if tracker and hasattr(tracker, 'get_activity'):
        tracker.get_activity()
    if detector and hasattr(detector, 'detect'):
        detector.detect()

    portfolio_id = kwargs.get('portfolio_id')
    ticker = kwargs.get('ticker')
    activity_payload = kwargs.get('activity_payload')
    anomaly_payload = kwargs.get('anomaly_payload')

    report_id = kwargs.get('report_id') or str(uuid.uuid4().hex)

    exposure_score = float(random.uniform(0.0, 100.0))
    if activity_payload and isinstance(activity_payload, dict):
        exposure_score = float(activity_payload.get("score", exposure_score))

    report_result = {
        "report_id": report_id,
        "status": "generated",
        "exposure_score": exposure_score,
        "portfolio_id": portfolio_id,
        "ticker": ticker,
        "activity_payload": activity_payload,
        "anomaly_payload": anomaly_payload
    }

    os.makedirs("reports", exist_ok=True)
    report_file_path = f"reports/insider_exposure_{report_id}.json"
    with open(report_file_path, "w", encoding="utf-8") as f:
        json.dump(report_result, f)

    save_report_state(report_result)

    return report_result