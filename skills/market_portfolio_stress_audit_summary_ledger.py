import os
import io
from skills.db_storage import db_storage


class MarketPortfolioStressAuditSummaryLedger:
    def __init__(self, db_storage_instance=None):
        self.db_storage = db_storage_instance if db_storage_instance is not None else db_storage

    def record_audit_summary(self, audit_payload: dict) -> bool:
        return self.db_storage.save_summary(audit_payload)

    def fetch_audit_summary(self, ledger_id: str) -> dict:
        record = self.db_storage.get_by_id(ledger_id)
        if record is None:
            raise ValueError(f"Audit summary not found for ledger_id: {ledger_id}")
        return record

    def export_audit_ledger(self) -> io.BytesIO:
        return self.db_storage.get_export_stream()


def market_portfolio_stress_audit_summary_ledger(initial_data: dict, db=None) -> dict:
    if db is None:
        db = db_storage

    portfolio_id = initial_data.get("portfolio_id")
    audit_id = initial_data.get("audit_id")
    stress_score = initial_data.get("stress_score")
    ledger_path = initial_data.get("ledger_path")

    if not portfolio_id or not audit_id or not isinstance(stress_score, (int, float)) or not ledger_path:
        raise ValueError("Invalid audit data provided")

    record = {
        "audit_id": audit_id,
        "portfolio_id": portfolio_id,
        "stress_score": stress_score
    }

    db.save(audit_id, record)

    with open(ledger_path, "w", encoding="utf-8") as f:
        f.write(f"Audit ID: {audit_id}\nPortfolio ID: {portfolio_id}\nStress Score: {stress_score}\n")

    return record
