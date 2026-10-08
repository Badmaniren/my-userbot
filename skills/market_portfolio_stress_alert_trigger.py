from skills import market_portfolio_stress_audit_summary_vault
from skills import market_portfolio_alert_dispatcher


def check_stress_thresholds_and_alert(
    storage_target,
    expected_audit_id,
    symbol,
    url,
    telegram_token,
    chat_id,
    severity_level,
    min_threshold,
    channels
):
    is_valid = market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_validate(
        storage_target, expected_audit_id
    )

    if not is_valid:
        return None

    if isinstance(is_valid, dict):
        audit_data = is_valid
    else:
        try:
            import json
            with open(storage_target, "r", encoding="utf-8") as f:
                audit_data = json.load(f)
        except Exception:
            return None

    status = audit_data.get("status", "")
    max_drawdown = audit_data.get("max_drawdown")
    if max_drawdown is None:
        max_drawdown = audit_data.get("drawdown", 0.0)

    is_breach = (
        status in ["BREACH", "BREACH_DETECTED"] or
        (max_drawdown is not None and max_drawdown > min_threshold)
    )

    if is_breach:
        market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol,
            url,
            telegram_token,
            chat_id,
            storage_target,
            severity_level,
            min_threshold,
            channels
        )
        return True
    else:
        return False


def run(
    storage_file,
    expected_audit_id,
    symbol,
    url,
    telegram_token,
    chat_id,
    severity_level,
    min_threshold,
    channels
):
    try:
        market_portfolio_stress_audit_summary_vault.start_new(storage_file)
    except TypeError:
        try:
            market_portfolio_stress_audit_summary_vault.start_new()
        except ValueError:
            pass

    return check_stress_thresholds_and_alert(
        storage_target=storage_file,
        expected_audit_id=expected_audit_id,
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        severity_level=severity_level,
        min_threshold=min_threshold,
        channels=channels
    )