import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_stress_audit_scheduler_hub import StressAuditSchedulerHub, market_portfolio_stress_audit_scheduler_hub_process

class TestStressAuditSchedulerHub(unittest.TestCase):

    def setUp(self):
        self.hub = StressAuditSchedulerHub()
        self.portfolio_id = uuid.uuid4().hex
        self.threshold = random.uniform(0.01, 0.99)
        self.storage_target = f"/tmp/{uuid.uuid4().hex}.json"

    def test_run_audit_cycle_success(self):
        expected_res = {"status": "triggered", "id": uuid.uuid4().hex}
        
        with patch('skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.evaluate_and_trigger') as mock_trigger:
            with patch('skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process') as mock_vault:
                mock_trigger.return_value = expected_res
                
                result = self.hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)
                
                self.assertEqual(result, expected_res)
                mock_vault.assert_called_once_with(self.storage_target, expected_res)

    def test_get_feed_exception_handling(self):
        feed_url = f"https://{uuid.uuid4().hex}.com/feed"
        
        with patch('skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.fetch_external_stress_feed') as mock_fetch:
            mock_fetch.side_effect = Exception("Network failure")
            
            result = self.hub.get_feed(feed_url)
            self.assertEqual(result, b"")

    def test_dispatch_alert_and_check_logic(self):
        audit_id = uuid.uuid4().hex
        message = uuid.uuid4().hex
        export_format = random.choice(['json', 'csv', 'xml'])
        expected_export = {uuid.uuid4().hex: random.randint(1, 100)}
        
        with patch('skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.notify_audit_system') as mock_notify:
            with patch('skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate') as mock_val:
                with patch('skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export') as mock_exp:
                    mock_notify.return_value = True
                    mock_val.return_value = True
                    mock_exp.return_value = expected_export
                    
                    res = self.hub.dispatch_alert_and_check(audit_id, message, self.storage_target, export_format)
                    
                    self.assertTrue(res['is_valid'])
                    self.assertEqual(res['export_data'], expected_export)
                    mock_notify.assert_called_with(audit_id, message)

    def test_process_hub_integration(self):
        audit_data = {"audit_log": uuid.uuid4().hex}
        
        with patch('skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub.run_audit_cycle') as mock_run:
            with patch('skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process') as mock_vault:
                mock_run.return_value = {"trigger": "success"}
                
                result = market_portfolio_stress_audit_scheduler_hub_process(
                    self.portfolio_id, self.threshold, self.storage_target, audit_data
                )
                
                self.assertEqual(result['trigger_result']['trigger'], "success")
                mock_vault.assert_called_with(self.storage_target, audit_data)

if __name__ == '__main__':
    unittest.main()