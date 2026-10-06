import hashlib
import json
import requests
from skills.db_storage import get_audit_logs_by_portfolio, save_audit_log_batch


class AuditChainValidator:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def validate_chain(self, table_name: str) -> bool:
        if self.db_storage is None:
            logs = get_audit_logs_by_portfolio(table_name)
        else:
            logs = self.db_storage.fetch_logs(table_name)

        if not logs:
            return True

        for i, log in enumerate(logs):
            record_id = log.get("id") or log.get("event_id")
            payload = log.get("payload") or log.get("action", "")
            prev_hash = log.get("prev_hash") or log.get("previous_hash", "0" * 64)
            current_hash = log.get("hash")

            if i == 0:
                expected_prev = "0" * 64
                if prev_hash != expected_prev:
                    raise ValueError("Invalid previous hash for the first block")
            else:
                prev_log = logs[i - 1]
                expected_prev = prev_log.get("hash") or prev_log.get("current_hash")
                if prev_hash != expected_prev:
                    raise ValueError(f"Broken hash chain at index {i}")

            if current_hash:
                raw_str = f"{prev_hash}:{record_id}:{payload}"
                calculated_hash = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()
                if calculated_hash != current_hash:
                    raise ValueError(f"Hash mismatch at index {i}")

        return True

    def verify_sequence(self, stream_id: str) -> bool:
        logs = self.db_storage.fetch_stream(stream_id)
        if not logs:
            return True

        expected_seq = logs[0].get("sequence")
        for log in logs:
            current_seq = log.get("sequence")
            if current_seq != expected_seq:
                raise RuntimeError("Sequence discontinuity detected")
            expected_seq += 1

        return True

    def extract_and_verify_stream_token(self, url: str) -> str:
        response = requests.get(url)
        content = response.raw.read()
        data = json.loads(content.decode('utf-8'))
        return data.get("token")


def validate_audit_chain(portfolio_id: str) -> dict:
    logs = get_audit_logs_by_portfolio(portfolio_id)
    if not logs:
        return {"is_valid": True}

    is_valid = True
    broken_index = None

    for i in range(1, len(logs)):
        prev_log = logs[i - 1]
        curr_log = logs[i]

        expected_prev_hash = prev_log.get("hash") or prev_log.get("event_id", "")
        actual_prev_hash = curr_log.get("previous_hash") or curr_log.get("prev_hash")

        if not actual_prev_hash or actual_prev_hash != expected_prev_hash:
            is_valid = False
            broken_index = i
            break

    return {
        "is_valid": is_valid,
        "broken_index": broken_index
    }