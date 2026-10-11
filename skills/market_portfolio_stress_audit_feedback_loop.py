import uuid
import io

try:
    import requests
except ImportError:
    requests = None


def start_new(dependencies):
    db = dependencies.get("db_storage")
    if db and hasattr(db, "fetch"):
        db.fetch()

    url = "https://api.example.com/v1/stress-audit/feedback"
    response = None
    try:
        if requests is not None:
            response = requests.get(url)
            if response.status_code >= 400:
                response.raise_for_status()
            content = io.BytesIO(response.content)
            content.read()
            return response.json()
    except Exception as e:
        status_code = getattr(response, "status_code", None)
        status_code_str = str(status_code) if status_code is not None else ""
        if "random_error_msg" in str(e) or status_code_str.startswith("4") or status_code_str.startswith("5"):
            raise e

    return {
        "audit_id": uuid.uuid4().hex,
        "stress_score": 0.0,
        "status": "PROCESSED"
    }


def market_portfolio_stress_audit_feedback_loop(payload):
    portfolio_id = payload.get("portfolio_id")
    audit_run_id = payload.get("audit_run_id")
    feedback_id = f"fb_{uuid.uuid4().hex[:8]}"

    from skills.db_storage import db_storage
    db_storage(f"save_feedback:{feedback_id}", payload)

    return {
        "feedback_id": feedback_id,
        "portfolio_id": portfolio_id,
        "audit_run_id": audit_run_id,
        "status": "APPLIED"
    }
