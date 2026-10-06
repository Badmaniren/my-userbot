from skills.db_storage import db_storage, DbStorage


class MarketPortfolioAuditIntegrityReporter:
    def __init__(self, db_storage=None, **dependencies):
        self.db_storage = db_storage if db_storage is not None else globals()["db_storage"]
        self.dependencies = dependencies

    def generate_audit_report(self, audit_id: str) -> dict:
        if not audit_id:
            raise ValueError("Audit ID cannot be empty")

        record = self.db_storage.get_audit_record(audit_id)
        if not record:
            raise LookupError(f"Audit record {audit_id} not found in storage")

        discrepancies = record.get("discrepancies", [])
        report = {
            "audit_id": audit_id,
            "status": "FAILED" if discrepancies else "PASSED",
            "discrepancies_count": len(discrepancies),
            "details": discrepancies
        }

        self.db_storage.save_integrity_report(audit_id, report)
        return report


def market_portfolio_audit_integrity_reporter(reporter_input: dict) -> dict:
    portfolio_id = reporter_input.get("portfolio_id")
    audit_session_id = reporter_input.get("audit_session_id")
    report_data = reporter_input.get("report_data", {})
    discrepancy_detected = reporter_input.get("discrepancy_detected", False)

    discrepancy_value = report_data.get("discrepancy", 0.0) if discrepancy_detected else 0.0

    integrity_output = {
        "portfolio_id": portfolio_id,
        "audit_session_id": audit_session_id,
        "discrepancy": discrepancy_value,
        "status": "FAILED" if discrepancy_detected else "PASSED",
        "report_data": report_data
    }

    db_query = {
        "action": "save_integrity_audit",
        "portfolio_id": portfolio_id,
        "audit_session_id": audit_session_id,
        "discrepancy": discrepancy_value,
        "record": integrity_output
    }
    db_storage(db_query)

    return integrity_output
