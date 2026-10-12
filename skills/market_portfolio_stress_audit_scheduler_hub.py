from typing import Optional, Dict, Any
from skills.market_portfolio_stress_auto_rebalance_trigger import StressAutoRebalanceTrigger
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)


class StressAuditSchedulerHub:
    def __init__(self, **kwargs):
        self.trigger = kwargs.get("trigger") or StressAutoRebalanceTrigger(**kwargs)

    def run_audit_cycle(self, portfolio_id: str, threshold: float, storage_target: str) -> Optional[Dict[str, Any]]:
        if not isinstance(portfolio_id, str):
            raise TypeError("portfolio_id must be a string")
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
            raise TypeError("threshold must be a float or int")
        if not isinstance(storage_target, str):
            raise TypeError("storage_target must be a string")

        res = self.trigger.evaluate_and_trigger(portfolio_id, threshold)
        if res is not None:
            market_portfolio_stress_audit_summary_vault_process(storage_target, res)
        return res

    def get_feed(self, feed_url: str) -> bytes:
        if not isinstance(feed_url, str):
            raise TypeError("feed_url must be a string")
        try:
            return self.trigger.fetch_external_stress_feed(feed_url)
        except Exception:
            return b""

    def dispatch_alert_and_check(self, audit_id: str, message: str, storage_target: str, export_format: str) -> Dict[str, Any]:
        if not isinstance(audit_id, str):
            raise TypeError("audit_id must be a string")
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        if not isinstance(storage_target, str):
            raise TypeError("storage_target must be a string")
        if not isinstance(export_format, str):
            raise TypeError("export_format must be a string")

        notification_res = self.trigger.notify_audit_system(audit_id, message)

        try:
            is_valid = market_portfolio_stress_audit_summary_vault_validate(storage_target, audit_id)
        except Exception:
            is_valid = False

        try:
            export_data = market_portfolio_stress_audit_summary_vault_export(storage_target, export_format)
        except Exception:
            export_data = {}

        return {
            "notification": notification_res,
            "is_valid": is_valid,
            "export_data": export_data
        }


def market_portfolio_stress_audit_scheduler_hub_process(
    portfolio_id: str, threshold: float, storage_target: str, audit_data: dict
) -> Dict[str, Any]:
    if not isinstance(portfolio_id, str):
        raise TypeError("portfolio_id must be a string")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        raise TypeError("threshold must be a float or int")
    if not isinstance(storage_target, str):
        raise TypeError("storage_target must be a string")
    if not isinstance(audit_data, dict):
        raise TypeError("audit_data must be a dictionary")

    scheduler = StressAuditSchedulerHub()
    trigger_result = scheduler.run_audit_cycle(portfolio_id, threshold, storage_target)

    market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data)

    return {
        "trigger_result": trigger_result,
        "vault_storage": storage_target
    }
