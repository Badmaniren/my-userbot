from skills.market_portfolio_stress_auto_rebalance_trigger import StressAutoRebalanceTrigger
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)


class StressAuditSchedulerHub:
    """
    Центральный узел агрегации потоковой телеметрии.
    Обеспечивает взаимодействие между триггерами ребалансировки и хранилищем аудита.
    """
    def __init__(self):
        self.trigger = StressAutoRebalanceTrigger()

    def run_audit_cycle(self, portfolio_id, threshold, storage_target):
        res = self.trigger.evaluate_and_trigger(portfolio_id, threshold)
        audit_payload = res if isinstance(res, dict) else {"portfolio_id": portfolio_id, "threshold": threshold}
        market_portfolio_stress_audit_summary_vault_process(storage_target, audit_payload)
        return res

    def get_feed(self, feed_url):
        try:
            return self.trigger.fetch_external_stress_feed(feed_url)
        except Exception:
            return b""

    def dispatch_alert_and_check(self, audit_id, message, storage_target, export_format):
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


def market_portfolio_stress_audit_scheduler_hub_process(portfolio_id, threshold, storage_target, audit_data):
    """
    Точка входа для обработки цикла аудита с интеграцией в хранилище.
    """
    scheduler = StressAuditSchedulerHub()
    trigger_result = scheduler.run_audit_cycle(portfolio_id, threshold, storage_target)
    
    market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data)
    
    return {
        "trigger_result": trigger_result,
        "vault_storage": storage_target
    }