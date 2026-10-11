import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_audit_summary_vault import start_new

class TestMarketPortfolioStressAuditSummaryVaultStartNew(unittest.TestCase):

    def test_start_new_missing_db_storage_raises_value_error(self):
        rand_key = f"dep_{uuid.uuid4().hex[:6]}"
        rand_val = MagicMock()
        with self.assertRaises(ValueError):
            start_new(**{rand_key: rand_val})

    def test_start_new_extracts_dependencies(self):
        db_storage = MagicMock()
        rand_uuid = uuid.uuid4().hex
        db_storage.save.return_value = rand_uuid
        
        mock_dep = MagicMock()
        rand_kwarg_name = f"extractor_{uuid.uuid4().hex[:6]}"
        
        kwargs = {
            "db_storage": db_storage,
            rand_kwarg_name: mock_dep
        }
        
        result = start_new(**kwargs)
        mock_dep.extract.assert_called_once()
        self.assertEqual(result["save_result"], rand_uuid)

    def test_start_new_default_payload_when_reporter_none(self):
        db_storage = MagicMock()
        rand_uuid = uuid.uuid4().hex
        db_storage.save.return_value = rand_uuid
        
        stress_reporter = MagicMock()
        stress_reporter.generate.return_value = None
        
        kwargs = {
            "db_storage": db_storage,
            "market_portfolio_stress_reporter": stress_reporter
        }
        
        result = start_new(**kwargs)
        self.assertEqual(result["payload"], {"status": "ok"})
        self.assertEqual(result["save_result"], rand_uuid)

    def test_start_new_invalid_payload_type_raises_type_error(self):
        db_storage = MagicMock()
        rand_str_payload = "".join(random.choices(string.ascii_letters, k=10))
        
        stress_reporter = MagicMock()
        stress_reporter.generate.return_value = rand_str_payload
        
        kwargs = {
            "db_storage": db_storage,
            "market_portfolio_stress_reporter": stress_reporter
        }
        
        with self.assertRaises(TypeError):
            start_new(**kwargs)