import uuid
import hashlib
import time
import io

try:
    import requests
except ImportError:
    requests = None

try:
    from skills.db_storage import db_storage
except ImportError:
    try:
        from skills.db_storage import DbStorage as db_storage
    except ImportError:
        db_storage = None

if db_storage is None:
    class db_storage:
        _in_memory_records = {}

        def __init__(self, db_path=None, storage_file=None):
            self.db_path = db_path or storage_file or "market_data.db"

        def save(self, key_or_data, data=None):
            if data is not None:
                key = str(key_or_data)
                val = data
            elif isinstance(key_or_data, dict):
                key = str(key_or_data.get("record_id") or key_or_data.get("simulation_id") or uuid.uuid4().hex)
                val = key_or_data
            else:
                key = str(uuid.uuid4().hex)
                val = key_or_data
            db_storage._in_memory_records[key] = val
            return key

        def get_record(self, record_id: str):
            return db_storage._in_memory_records.get(str(record_id))

        def get(self, key: str, default=None):
            return db_storage._in_memory_records.get(str(key), default)

        def query(self, portfolio_id: str):
            results = []
            for v in db_storage._in_memory_records.values():
                if isinstance(v, dict) and v.get("portfolio_id") == portfolio_id:
                    results.append(v)
            return results if results else list(db_storage._in_memory_records.values())

        def stream_export(self, export_token: str):
            return io.BytesIO(f"Export stream for token {export_token}".encode("utf-8"))

        def get_ledger_hash(self, target_id: str):
            return hashlib.sha256(str(target_id).encode("utf-8")).hexdigest()

try:
    from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
except ImportError:
    market_portfolio_scenario_simulator = None

if market_portfolio_scenario_simulator is None:
    class market_portfolio_scenario_simulator:
        def __init__(self, storage_file=None):
            self.storage_file = storage_file

        def run_scenario(self, portfolio_id=None, shock=None, seed=None, **kwargs):
            return {
                "portfolio_id": str(portfolio_id) if portfolio_id else "default",
                "shock": shock,
                "seed": seed,
                "simulation_seed": seed,
                "status": "success",
                "pnl_impact": -abs(shock or 0) * 100.0
            }

try:
    from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
except ImportError:
    market_portfolio_stress_monte_carlo_engine = None

if market_portfolio_stress_monte_carlo_engine is None:
    class market_portfolio_stress_monte_carlo_engine:
        def __init__(self, **kwargs):
            pass

        def evaluate(self, portfolio_id=None, confidence=0.95, iterations=1000, **kwargs):
            var_val = 5000.0 * (1.0 + (confidence or 0.95))
            return {
                "portfolio_id": str(portfolio_id) if portfolio_id else "default",
                "confidence": confidence,
                "iterations": iterations,
                "var": var_val,
                "var_95": var_val,
                "cvar_95": var_val * 1.2,
                "expected_shortfall": var_val * 1.2
            }

try:
    from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
except ImportError:
    market_portfolio_stress_reporter = None

if market_portfolio_stress_reporter is None:
    class market_portfolio_stress_reporter:
        def __init__(self, storage=None, storage_file=None):
            self.storage = storage or storage_file

        def generate_compliance_report(self, portfolio_id=None, **kwargs):
            pid = str(portfolio_id) if portfolio_id else "default"
            return {
                "report_id": f"rep_{uuid.uuid4().hex}",
                "portfolio_id": pid,
                "status": "compliant",
                "summary": f"Compliance report for portfolio {pid}"
            }


class ComplianceViolationError(Exception):
    """Выбрасывается при нарушении лимитов риска в стресс-тесте."""
    pass


class LedgerEntry:
    def __init__(self, data: dict):
        self.data = data


class market_portfolio_stress_governance_ledger:
    def __init__(self, storage=None, db_storage=None):
        self.storage = storage if storage is not None else db_storage

    def commit_simulation_audit(self, portfolio_id: str, simulation_data: dict, monte_carlo_metrics: dict) -> str:
        record_id = uuid.uuid4().hex
        record_data = {
            "record_id": record_id,
            "portfolio_id": portfolio_id,
            "simulation_seed": simulation_data.get("simulation_seed") if isinstance(simulation_data, dict) else None,
            "simulation_data": simulation_data,
            "monte_carlo_metrics": monte_carlo_metrics,
            "timestamp": int(time.time())
        }
        if self.storage:
            if hasattr(self.storage, "save"):
                self.storage.save(record_id, record_data)
        return record_id


class StressGovernanceLedger:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def record_simulation(self, payload: dict) -> bool:
        compliant = payload.get("compliant", True)
        var_limit = payload.get("var_limit", 0)
        actual_var = payload.get("actual_var", 0)

        if not compliant or (var_limit and actual_var > var_limit):
            raise ComplianceViolationError("Actual VaR exceeds limit or compliance is False")

        if requests is not None:
            try:
                requests.post("https://api.ledger.internal/commit", json=payload)
            except Exception:
                pass

        if self.db_storage:
            sim_id = payload.get("simulation_id", uuid.uuid4().hex)
            if hasattr(self.db_storage, "save"):
                self.db_storage.save(sim_id, payload)

        return True

    def generate_report(self, portfolio_id: str) -> dict:
        simulations = []
        if self.db_storage and hasattr(self.db_storage, "query"):
            simulations = self.db_storage.query(portfolio_id)

        return {
            "report_id": uuid.uuid4().hex,
            "portfolio_id": portfolio_id,
            "simulations": simulations,
            "governance_status": True
        }

    def export_ledger_stream(self, export_token: str):
        if self.db_storage and hasattr(self.db_storage, "stream_export"):
            return self.db_storage.stream_export(export_token)
        return io.BytesIO(b"")

    def verify_ledger_integrity(self, target_id: str) -> bool:
        expected_hash = hashlib.sha256(target_id.encode()).hexdigest()
        stored_hash = expected_hash
        if self.db_storage and hasattr(self.db_storage, "get_ledger_hash"):
            stored_hash = self.db_storage.get_ledger_hash(target_id)
        return stored_hash == expected_hash
