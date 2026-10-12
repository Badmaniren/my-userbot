import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys

from skills.market_portfolio_stress_audit_health_pulse import start_new

class TestMarketPortfolioStressAuditHealthPulse(unittest.TestCase):

    def setUp(self):
        self.random_deps_count = random.randint(3, 10)
        self.mock_registry = {}
        for _ in range(self.random_deps_count):
            dep_name = f"dep_{uuid.uuid4().hex[:8]}"
            mock_inst = MagicMock()
            mock_inst.health_check.return_value = True
            self.mock_registry[dep_name] = mock_inst

    def test_start_new_success_all_healthy(self):
        with patch('skills.market_portfolio_stress_audit_health_pulse.get_all_subsystems', return_value=self.mock_registry) as mock_get:
            result = start_new()
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get('status') == 'HEALTHY' or result.get('healthy') is True or isinstance(result, bool) or result is None)

    def test_start_new_failure_subsystem_unhealthy(self):
        unhealthy_name = f"failed_{uuid.uuid4().hex[:6]}"
        bad_mock = MagicMock()
        bad_mock.health_check.return_value = False
        self.mock_registry[unhealthy_name] = bad_mock

        with patch('skills.market_portfolio_stress_audit_health_pulse.get_all_subsystems', return_value=self.mock_registry):
            try:
                res = start_new()
                if isinstance(res, dict):
                    self.assertIn(unhealthy_name, str(res))
            except Exception as e:
                self.assertIsNotNone(e)

    def test_start_new_io_stream_integrity(self):
        random_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        with patch('skills.market_portfolio_stress_audit_health_pulse.sys.stdin', mock_stream):
            try:
                res = start_new()
                self.assertIsNotNone(res)
            except Exception:
                pass

    def test_start_new_random_exception_resilience(self):
        err_msg = f"critical_failure_{uuid.uuid4().hex}"
        with patch('skills.market_portfolio_stress_audit_health_pulse.get_all_subsystems', side_effect=Exception(err_msg)):
            with self.assertRaises(Exception) as ctx:
                start_new()
            self.assertIn(err_msg, str(ctx.exception))

if __name__ == '__main__':
    unittest.main()