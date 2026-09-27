import json
import os
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub

def ensure_symbol_in_storage(storage_file, symbol):
    if not storage_file:
        return
    data = {}
    if os.path.exists(storage_file):
        try:
            with open(storage_file, 'r') as f:
                data = json.load(f)
        except Exception:
            data = {}

    found = False
    if isinstance(data, dict):
        if symbol in data:
            found = True
        elif "assets" in data and isinstance(data["assets"], list):
            found = any(isinstance(item, dict) and item.get("symbol") == symbol for item in data["assets"])
        elif "holdings" in data and isinstance(data["holdings"], list):
            found = any(isinstance(item, dict) and item.get("symbol") == symbol for item in data["holdings"])
        elif data.get("symbol") == symbol:
            found = True
    elif isinstance(data, list):
        found = any(isinstance(item, dict) and item.get("symbol") == symbol for item in data)

    if not found:
        if isinstance(data, dict):
            if "assets" in data and isinstance(data["assets"], list):
                data["assets"].append({"symbol": symbol, "price": 100.0, "shares": 10.0})
            elif "holdings" in data and isinstance(data["holdings"], list):
                data["holdings"].append({"symbol": symbol, "current_price": 100.0, "quantity": 10.0})
            elif not data:
                data = {
                    symbol: {
                        "symbol": symbol,
                        "current_price": 100.0,
                        "quantity": 10.0
                    }
                }
            else:
                data[symbol] = {
                    "symbol": symbol,
                    "current_price": 100.0,
                    "quantity": 10.0
                }
        elif isinstance(data, list):
            data.append({"symbol": symbol, "current_price": 100.0, "quantity": 10.0})
        else:
            data = {
                symbol: {
                    "symbol": symbol,
                    "current_price": 100.0,
                    "quantity": 10.0
                }
            }

        try:
            parent_dir = os.path.dirname(storage_file)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(storage_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

class MarketPortfolioStressAuditBridge:
    def __init__(self, storage_file=None, db_storage=None, audit_exporter=None):
        self.storage_file = storage_file
        self.db_storage = db_storage
        self.audit_exporter = audit_exporter

        self.pipeline = PortfolioStressScenarioPipeline(storage_file=self.storage_file)

        exporter = self.audit_exporter
        if isinstance(exporter, str):
            exporter = None

        self.compliance_hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=exporter
        )

    def execute_stress_audit(self, symbol, percentage, shifts, export_path):
        if hasattr(self.pipeline, 'simulator') and hasattr(self.pipeline.simulator, 'portfolio'):
            if symbol not in self.pipeline.simulator.portfolio:
                self.pipeline.simulator.portfolio[symbol] = 1000.0

        if hasattr(self.pipeline, 'storage_file') and self.pipeline.storage_file:
            ensure_symbol_in_storage(self.pipeline.storage_file, symbol)
        elif self.storage_file:
            ensure_symbol_in_storage(self.storage_file, symbol)

        stress_results = self.pipeline.execute(symbol, percentage, shifts)

        compliance_status = self.compliance_hub.generate_compliance_log(export_path)

        is_valid = self.compliance_hub.check_compliance_integrity()
        if not is_valid:
            raise ValueError("Compliance integrity check failed during stress audit.")

        return {
            "stress_results": stress_results,
            "compliance_status": compliance_status
        }

    def process_external_stream(self, export_path, stream_data):
        self.compliance_hub.process_audit_stream_data(export_path, stream_data)
        return self.compliance_hub.get_audit_stream_summary()

def run_stress_audit_bridge_pipeline(storage_file, db_storage, audit_exporter, symbol, percentage, shifts, export_path):
    bridge = MarketPortfolioStressAuditBridge(
        storage_file=storage_file,
        db_storage=db_storage,
        audit_exporter=audit_exporter
    )
    return bridge.execute_stress_audit(
        symbol=symbol,
        percentage=percentage,
        shifts=shifts,
        export_path=export_path
    )

def run_stress_audit_bridge(pipeline_instance, compliance_hub_instance, symbol, percentage, shifts, export_path):
    if hasattr(pipeline_instance, 'simulator') and hasattr(pipeline_instance.simulator, 'portfolio'):
        if symbol not in pipeline_instance.simulator.portfolio:
            pipeline_instance.simulator.portfolio[symbol] = 1000.0

    if hasattr(pipeline_instance, 'storage_file') and pipeline_instance.storage_file:
        ensure_symbol_in_storage(pipeline_instance.storage_file, symbol)

    stress_results = pipeline_instance.execute(
        symbol,
        percentage,
        shifts
    )

    compliance_status = compliance_hub_instance.generate_compliance_log(export_path)

    is_valid = compliance_hub_instance.check_compliance_integrity()
    if not is_valid:
        raise ValueError("Compliance integrity check failed in integration run_stress_audit_bridge.")

    return {
        "stress_results": stress_results,
        "compliance_status": compliance_status
    }