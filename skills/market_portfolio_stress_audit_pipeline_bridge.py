from skills import market_portfolio_stress_audit_summary_vault as vault
from skills import market_portfolio_stress_audit_visualizer as visualizer
from skills import market_portfolio_stress_audit_scheduler_hub as scheduler


class DefaultDbStorage:
    def save(self, payload):
        return {"status": "saved"}


class MarketPortfolioStressAuditPipelineBridge:
    def __init__(self, storage_target=None, db_storage=None):
        self.storage_target = storage_target
        self.db_storage = db_storage or DefaultDbStorage()

    def initialize_audit(self, **kwargs):
        opts = dict(kwargs)
        opts.setdefault("db_storage", self.db_storage)
        return vault.start_new(**opts)

    def visualize_audit(self, payload):
        vis_instance = visualizer.MarketPortfolioStressAuditVisualizer()
        return vis_instance.visualize(payload)


def run_stress_audit_pipeline(payload):
    storage_target = payload.get("storage_target")
    expected_audit_id = payload.get("expected_audit_id")
    db_storage = payload.get("db_storage") or DefaultDbStorage()

    audit_data = payload.get("audit_data")
    if audit_data is None:
        audit_data = payload.get("audit_stream")

    fmt = payload.get("format", "json")

    start_res = vault.start_new(db_storage=db_storage)

    audit_id = expected_audit_id
    if not audit_id:
        if isinstance(start_res, dict):
            audit_id = start_res.get("audit_id") or start_res.get("save_result")
        else:
            audit_id = start_res

    vault.market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data)
    vault.market_portfolio_stress_audit_summary_vault_validate(storage_target, audit_id)
    vault.market_portfolio_stress_audit_summary_vault_export(storage_target, fmt)

    visualizer.market_portfolio_stress_audit_visualizer(payload)

    return {"audit_id": audit_id, "status": "success"}


def market_portfolio_stress_audit_pipeline_bridge(payload):
    storage_target = payload.get("storage_target")
    audit_id = payload.get("audit_id")
    metrics = payload.get("metrics")
    db_storage = payload.get("db_storage") or DefaultDbStorage()

    vault.start_new(db_storage=db_storage)

    vault.market_portfolio_stress_audit_summary_vault_process(storage_target, metrics)
    vault.market_portfolio_stress_audit_summary_vault_validate(storage_target, audit_id)
    vault.market_portfolio_stress_audit_summary_vault_export(storage_target, "json")

    vis_instance = visualizer.MarketPortfolioStressAuditVisualizer()
    vis_instance.visualize(payload)

    return {"audit_id": audit_id, "result": "completed"}
