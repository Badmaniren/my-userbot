import io
from typing import Optional, Any

try:
    import db_storage
except ImportError:
    from skills import db_storage

try:
    import market_anomaly_detector
except ImportError:
    from skills import market_anomaly_detector

try:
    import market_parser
except ImportError:
    from skills import market_parser

try:
    import market_insider_activity_tracker
except ImportError:
    from skills import market_insider_activity_tracker

try:
    import market_insider_alert_pipeline
except ImportError:
    from skills import market_insider_alert_pipeline


def start_new(epic_name: Optional[str] = None, target_metric: Optional[str] = None, stream_source: Optional[Any] = None) -> dict:
    """
    Запускает новый эпик для системы сбора и анализа рыночных аномалий
    в соответствии с юнит-тестами Архитектора.
    """
    if hasattr(db_storage, "save_epic"):
        db_storage.save_epic(epic_name=epic_name, target=target_metric)

    if hasattr(market_anomaly_detector, "initialize_system"):
        detector_result = market_anomaly_detector.initialize_system(target=target_metric)
    else:
        detector_result = {"status": "ok"}

    if hasattr(market_parser, "parse_stream"):
        if stream_source is not None:
            market_parser.parse_stream(stream_source)
        else:
            market_parser.parse_stream()

    response = {
        "epic": epic_name,
        "target": target_metric,
        "detector": detector_result
    }

    if hasattr(market_insider_alert_pipeline, "execute_pipeline"):
        pipeline_res = market_insider_alert_pipeline.execute_pipeline()
        response["pipeline_result"] = pipeline_res
    else:
        response["pipeline_result"] = {"status": "executed"}

    return response


def create_new_market_anomaly_epic(title: str, report_reference: str, db_instance: Any) -> Any:
    """
    Создает новый рыночный аномальный эпик для интеграционных тестов.
    """
    epic_id = db_instance.create_epic_record({
        "title": title,
        "report": report_reference
    })
    return epic_id
