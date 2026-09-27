import json
import os
from typing import Any, Dict, Optional

from skills.db_storage import db_storage


def market_insider_investigation_dossier_builder(payload: Dict[str, Any]) -> Dict[str, Any]:
    anomaly_id = payload.get("anomaly_id")
    ticker = payload.get("ticker")
    output_file = payload.get("output_file")

    dossier = {
        "anomaly_id": anomaly_id,
        "ticker": ticker,
        "dossier_status": "completed",
        "include_history": payload.get("include_history", True)
    }

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(dossier, f)

    return dossier


def start_new(target_id: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
    db_storage_dep = kwargs.get("db_storage")
    if db_storage_dep is not None:
        inv_data = db_storage_dep.fetch_investigation_data(target_id)
        if inv_data is None:
            return None

    extractor = kwargs.get("extractor_tool_1790087207")
    if extractor is not None:
        extractor.extract(target_id)

    detector = kwargs.get("market_anomaly_detector")
    if detector is not None:
        detector.analyze(target_id)

    pipeline = kwargs.get("market_insider_alert_pipeline")
    if pipeline is not None:
        pipeline.run(target_id)

    bridge = kwargs.get("market_insider_anomaly_report_bridge")
    if bridge is not None:
        bridge.build_report(target_id)

    return {
        "target_id": target_id,
        "status": "success"
    }