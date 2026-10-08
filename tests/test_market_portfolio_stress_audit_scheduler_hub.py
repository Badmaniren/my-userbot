import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
from skills.market_portfolio_stress_audit_scheduler_hub import StressAuditSchedulerHub, market_portfolio_stress_audit_scheduler_hub_process

class TestStressAuditSchedulerHub(unittest.TestCase):

    def setUp(self):
        self.hub = StressAuditSchedulerHub()
        self.portfolio_id = uuid.uuid4().hex
        self.threshold = random.uniform(0.01, 0.99)
        self.storage_target = f"/tmp/{uuid.uuid4().hex}.db"

    def test_run_audit_cycle_success(self):
        mock_res = {"audit_id": uuid.uuid4().hex, "status": "critical"}

        with patch('skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.evaluate_and_trigger') as mock_trigger:
            with patch('skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process') as mock_vault:
                mock_trigger.return_value = mock_res

                result = self.hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

                self.assertEqual(result, mock_res)
                mock_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
                mock_vault.assert_called_once_with(self.storage_target, mock_res)

    def test_get_feed_exception_handling(self):
        feed_url = f"https://{uuid.uuid4().hex}.com/feed"

        with patch('skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.fetch_external_stress_feed') as mock_fetch:
            mock_fetch.side_effect = Exception("Network failure")
            
            result = self.hub.get_feed(feed_url)
            
            self.assertEqual(result, b"")
            mock_fetch.assert_called_once_with(feed_url)

    def test_dispatch_alert_and_check_logic(self):
        audit_id = uuid.uuid4().hex
        message = "".join(random.choices(string.ascii_letters, k=20))
        export_format = random.choice(['json', 'csv', 'xml'])

        mock_notif = {"sent": True, "id": uuid.uuid4().hex}
        mock_export = {"data": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.notify_audit_system') as mock_notify:
            with patch('skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate') as mock_val:
                with patch('skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export') as mock_exp:
                    mock_notify.return_value = mock_notif
                    mock_val.return_value = True
                    mock_exp.return_value = mock_export

                    res = self.hub.dispatch_alert_and_check(audit_id, message, self.storage_target, export_format)

                    self.assertEqual(res["notification"], mock_notif)
                    self.assertTrue(res["is_valid"])
                    self.assertEqual(res["export_data"], mock_export)

    def test_scheduler_hub_process_integration(self):
        audit_data = {"payload": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub.run_audit_cycle') as mock_run:
            with patch('skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process') as mock_vault:
                expected_trigger_res = {"trigger": uuid.uuid4().hex}
                mock_run.return_value = expected_trigger_res

                result = market_portfolio_stress_audit_scheduler_hub_process(
                    self.portfolio_id, self.threshold, self.storage_target, audit_data
                )

                self.assertEqual(result["trigger_result"], expected_trigger_res)
                self.assertEqual(result["vault_storage"], self.storage_target)
                mock_vault.assert_called_once_with(self.storage_target, audit_data)

if __name__ == '__main__':
    unittest.main()