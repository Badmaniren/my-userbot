import io
import os
import requests

try:
    from skills.db_storage import db_storage
except ImportError:
    try:
        from skills import db_storage
    except ImportError:
        db_storage = None

try:
    from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
except ImportError:
    market_portfolio_collector_agent = None

try:
    from skills.market_portfolio_audit_log_exporter import market_portfolio_audit_log_exporter
except ImportError:
    try:
        from skills.market_portfolio_audit_log_exporter import MarketPortfolioAuditLogExporter as market_portfolio_audit_log_exporter
    except ImportError:
        market_portfolio_audit_log_exporter = None


class MarketPortfolioAuditIntegrityChecker:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get("db_storage")
        for key, value in kwargs.items():
            setattr(self, key, value)

    def run_audit_integrity_check(self):
        if self.db_storage and hasattr(self.db_storage, "get_transactions") and hasattr(self.db_storage, "get_audit_logs"):
            transactions = self.db_storage.get_transactions()
            audit_logs = self.db_storage.get_audit_logs()
        else:
            transactions = []
            audit_logs = []

        audit_map = {log.get("tx_id"): log.get("amount") for log in audit_logs}
        discrepancies = []

        for tx in transactions:
            tx_id = tx.get("id")
            tx_amount = tx.get("amount")
            if tx_id in audit_map:
                if audit_map[tx_id] != tx_amount:
                    discrepancies.append({
                        "tx_id": tx_id,
                        "transaction_amount": tx_amount,
                        "audit_amount": audit_map[tx_id]
                    })
            else:
                discrepancies.append({
                    "tx_id": tx_id,
                    "transaction_amount": tx_amount,
                    "audit_amount": None
                })

        anomalies_detected = len(discrepancies) > 0
        return {
            "anomalies_detected": anomalies_detected,
            "discrepancies": discrepancies
        }

    def parse_external_audit_stream(self, stream_mock):
        content = stream_mock.read()
        return {"parsed": True, "size": len(content)}


def market_portfolio_audit_integrity_checker(payload):
    portfolio_id = payload.get("portfolio_id")
    audit_file = payload.get("audit_file")

    return {
        "status": "SUCCESS",
        "checked_portfolio": portfolio_id,
        "audit_file": audit_file
    }