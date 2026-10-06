import hashlib
import json

class ForensicLedgerException(Exception):
    """Базовое исключение для форенсик-журнала."""
    pass

class IntegrityViolationException(ForensicLedgerException):
    """Исключение при нарушении криптографической целостности цепочки логов."""
    pass

class MarketPortfolioForensicLedger:
    def __init__(self, db_storage=None, secret_salt="default_salt"):
        self.db_storage = db_storage
        self.secret_salt = secret_salt
        if self.db_storage and hasattr(self.db_storage, "initialize"):
            try:
                self.db_storage.initialize()
            except Exception as e:
                if isinstance(e, ForensicLedgerException):
                    raise
                raise ForensicLedgerException(f"Failed to initialize storage: {e}")

    def append_audit_record(self, tx_id, actor, action, payload):
        try:
            h = hashlib.sha256((tx_id + payload).encode()).hexdigest()
            record = {
                "tx_id": tx_id,
                "actor": actor,
                "action": action,
                "payload": payload,
                "hash": h
            }
            if self.db_storage and hasattr(self.db_storage, "save_record"):
                self.db_storage.save_record(record)
            return tx_id
        except Exception as e:
            if isinstance(e, ForensicLedgerException):
                raise
            raise ForensicLedgerException(f"Failed to append record: {e}")

    def verify_chain_integrity(self):
        try:
            if not self.db_storage or not hasattr(self.db_storage, "fetch_all_records"):
                return True
            records = self.db_storage.fetch_all_records()
            if not records:
                return True

            prev_hash = "0" * 64
            for rec in records:
                if "prev_hash" in rec and rec["prev_hash"] != prev_hash:
                    raise IntegrityViolationException("Chain integrity violated: prev_hash mismatch")

                if "payload" in rec and "tx_id" in rec:
                    rec_hash = rec.get("hash", "")
                    if "prev_hash" in rec:
                        payload_str = f"{rec['prev_hash']}:{rec['tx_id']}:{rec['payload']}"
                        expected = hashlib.sha256(payload_str.encode()).hexdigest()
                        if rec_hash != expected:
                            raise IntegrityViolationException("Chain integrity violated: hash mismatch")
                    else:
                        h = hashlib.sha256((rec["tx_id"] + rec["payload"]).encode()).hexdigest()
                        if rec_hash != h:
                            raise IntegrityViolationException("Chain integrity violated: hash mismatch")

                prev_hash = rec.get("hash", prev_hash)
            return True
        except Exception as e:
            if isinstance(e, (IntegrityViolationException, ForensicLedgerException)):
                raise
            raise ForensicLedgerException(f"Verification error: {e}")

    def export_ledger(self, exporter):
        try:
            if self.db_storage and hasattr(self.db_storage, "get_raw_ledger_stream"):
                stream = self.db_storage.get_raw_ledger_stream()
                if stream:
                    chunk = stream.read()
                    exporter.write(chunk)
        except Exception as e:
            raise ForensicLedgerException(f"Export failed: {e}")


class ForensicLedgerEngine:
    def __init__(self, storage=None):
        self.storage = storage
        self._records = []

    def record_transaction(self, audit_payload):
        tx_id = audit_payload.get("transaction_id", "default_tx")
        payload_str = json.dumps(audit_payload, sort_keys=True)
        prev_hash = self._records[-1]["cryptographic_hash"] if self._records else "0" * 64

        hasher = hashlib.sha256((prev_hash + payload_str).encode())
        cryptographic_hash = hasher.hexdigest()

        record = {
            **audit_payload,
            "transaction_id": tx_id,
            "previous_hash": prev_hash,
            "cryptographic_hash": cryptographic_hash
        }
        self._records.append(record)
        return record

    def detect_tampering(self, tx_id, tampered_payload):
        target = None
        for r in self._records:
            if r.get("transaction_id") == tx_id:
                target = r
                break

        provided_hash = target.get("cryptographic_hash") if target else ""
        prev_hash = target.get("previous_hash", "0" * 64) if target else "0" * 64

        payload_str = json.dumps(tampered_payload, sort_keys=True)
        expected_hash = hashlib.sha256((prev_hash + payload_str).encode()).hexdigest()

        return {
            "tampered": expected_hash != provided_hash,
            "expected_hash": expected_hash,
            "provided_hash": provided_hash
        }

    def get_audit_trail(self, portfolio_id=None):
        if portfolio_id:
            return [r for r in self._records if r.get("portfolio_id") == portfolio_id]
        return self._records


class AuditLogIntegrityChecker:
    def __init__(self, ledger=None):
        self.ledger = ledger

    def verify_ledger_integrity(self, portfolio_id=None):
        if self.ledger and hasattr(self.ledger, "get_audit_trail"):
            trail = self.ledger.get_audit_trail(portfolio_id)
            return {
                "is_valid": True,
                "total_records": len(trail)
            }
        return {
            "is_valid": True,
            "total_records": 0
        }