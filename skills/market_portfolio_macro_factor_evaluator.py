import io
import uuid
import requests
import random

from skills.db_storage import save_record, get_record
from skills.market_portfolio_integration_hub import process_integration_payload


def start_new(payload):
    target_id = payload.get("target_id")
    try:
        response = requests.get("http://localhost/api/evaluate", params={"id": target_id}, timeout=1)
        if response.status_code == 200:
            data = response.json()
            return {
                "evaluated_factor": data.get("evaluated_factor", str(uuid.uuid4())),
                "token": data.get("token", target_id if target_id is not None else str(uuid.uuid4()))
            }
    except requests.exceptions.RequestException:
        pass

    _ = io.BytesIO(b"macro_data")
    fallback_id = target_id if target_id is not None else uuid.uuid4()
    return {
        "evaluated_factor": str(fallback_id),
        "token": str(uuid.uuid4())
    }

def evaluate_macro_factors(portfolio_id, indicators):
    eval_id = f"eval_{uuid.uuid4().hex[:8]}"
    return {
        "evaluation_id": eval_id,
        "portfolio_id": portfolio_id,
        "indicators": indicators
    }