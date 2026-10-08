from skills.market_portfolio_stress_auto_rebalance_trigger import StressAutoRebalanceTrigger
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)


class StressAuditSchedulerHub:
    def __init__(self):
        self.trigger = StressAutoRebalanceTrigger()

    def run_audit_cycle(self, portfolio_id, threshold, storage_target):
        res = self.trigger.evaluate_and_trigger(portfolio_id, threshold)
        if res is not None:
            market_portfolio_stress_audit_summary_vault_process(storage_target, res)
        return res

    def get_feed(self, feed_url):
        return self.trigger.fetch_external_stress_feed(feed_url)

    def dispatch_alert_and_check(self, audit_id, message, storage_target, export_format):
        notification_res = self.trigger.notify_audit_system(audit_id, message)
        is_valid = market_portfolio_stress_audit_summary_vault_validate(storage_target, audit_id)
        export_data = market_portfolio_stress_audit_summary_vault_export(storage_target, export_format)
        
        return {
            "notification": notification_res,
            "is_valid": is_valid,
            "export_data": export_data
        }


def market_portfolio_stress_audit_scheduler_hub_process(portfolio_id, threshold, storage_target, audit_data):
    scheduler = StressAuditSchedulerHub()
    trigger_result = scheduler.run_audit_cycle(portfolio_id, threshold, storage_target)
    
    market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data)
    
    return {
        "trigger_result": trigger_result,
        "vault_storage": storage_target
    }