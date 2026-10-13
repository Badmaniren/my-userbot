from skills import market_portfolio_stress_audit_summary_vault
from skills import market_portfolio_stress_audit_visualizer


class _DummyDBStorage:
    def save(self, payload):
        return True


def bundle_stress_audit_report(storage_target, audit_data):
    """
    Связывает хранилище стресс-аудитов с визуализатором для генерации
    структурированных сводных аудиторских бандлов с текстовыми графиками
    и метриками устойчивости.
    """
    db_obj = storage_target if (hasattr(storage_target, "save") and callable(getattr(storage_target, "save"))) else _DummyDBStorage()

    try:
        init_res = market_portfolio_stress_audit_summary_vault.start_new(db_storage=db_obj)
    except TypeError:
        try:
            init_res = market_portfolio_stress_audit_summary_vault.start_new(storage_target=storage_target)
        except TypeError:
            init_res = market_portfolio_stress_audit_summary_vault.start_new()

    if isinstance(init_res, str):
        audit_id = init_res
    elif isinstance(init_res, dict):
        audit_id = init_res.get("audit_id") or init_res.get("payload", {}).get("audit_id")
    else:
        audit_id = None

    if isinstance(audit_data, dict) and "audit_id" in audit_data:
        audit_id = audit_data["audit_id"]

    market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_process(
        storage_target=storage_target,
        audit_data=audit_data
    )

    visualizer = market_portfolio_stress_audit_visualizer.MarketPortfolioStressAuditVisualizer()
    text_chart = visualizer.visualize(audit_data)

    return {
        "audit_id": audit_id,
        "storage_target": storage_target,
        "text_chart": text_chart,
        "audit_data": audit_data
    }


def market_portfolio_stress_audit_report_bundler(bundle_payload):
    """
    Функциональный интерфейс для интеграционных тестов.
    Принимает словарь bundle_payload с ключами 'storage_path' (или 'storage_target'), 'audit_id', 'data'.
    """
    storage_target = bundle_payload.get("storage_path") or bundle_payload.get("storage_target") or "/default_target.json"
    audit_data = bundle_payload.get("data", bundle_payload)

    if isinstance(audit_data, dict):
        if "audit_id" in bundle_payload and "audit_id" not in audit_data:
            audit_data["audit_id"] = bundle_payload["audit_id"]

    return bundle_stress_audit_report(storage_target, audit_data)


class MarketPortfolioStressAuditReportBundler:
    """
    Классовый интерфейс для интеграционных тестов.
    """
    def __init__(self):
        pass

    def bundle(self, bundle_payload):
        return market_portfolio_stress_audit_report_bundler(bundle_payload)