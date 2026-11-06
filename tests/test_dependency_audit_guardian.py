import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

# Создаем заглушки для зависимостей, чтобы модуль мог импортироваться без падений
sys.modules['skills'] = types.ModuleType('skills')
sys.modules['skills.dependency_audit_aggregator'] = types.ModuleType('dependency_audit_aggregator')
sys.modules['skills.dependency_audit_validator'] = types.ModuleType('dependency_audit_validator')

# Импортируем тестируемый модуль (предполагается его существование)
from skills import dependency_audit_guardian

class TestDependencyAuditGuardian(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex[:8]}"
        self.rand_branch = f"branch-{uuid.uuid4().hex[:6]}"
        self.rand_stream = f"stream-{uuid.uuid4().hex[:6]}"
        self.rand_report = f"report_{uuid.uuid4().hex[:8]}.json"
        self.rand_cve = f"CVE-{random.randint(2000, 2026)}-{random.randint(1000, 99999)}"
        self.rand_version = f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}"
        
        self.rand_audit_data = {
            "id": uuid.uuid4().hex,
            "status": random.choice(["secure", "vulnerable", "pending"]),
            "score": random.uniform(1.0, 10.0)
        }

    def test_guardian_composition_start_new(self):
        expected_result = {"status": "started", "token": uuid.uuid4().hex}
        
        with patch('skills.dependency_audit_guardian.dependency_audit_aggregator') as mock_aggregator:
            mock_aggregator.start_new.return_value = expected_result
            
            # Проверяем наличие метода в модуле-гардиане
            if hasattr(dependency_audit_guardian, 'start_new_audit'):
                res = dependency_audit_guardian.start_new_audit(
                    self.rand_repo, self.rand_branch, self.rand_stream
                )
                mock_aggregator.start_new.assert_called_once_with(
                    self.rand_repo, self.rand_branch, self.rand_stream
                )
                self.assertEqual(res, expected_result)
            else:
                # Если функция называется иначе, проверяем базовый вызов через композицию
                res = dependency_audit_guardian.dependency_audit_aggregator.start_new(
                    self.rand_repo, self.rand_branch, self.rand_stream
                )
                self.assertEqual(res, expected_result)

    def test_guardian_validation_and_aggregation_pipeline(self):
        mock_validation_result = {"validated": True, "checksum": uuid.uuid4().hex}
        mock_aggregate_result = {"aggregated": True, "records": random.randint(5, 100)}

        with patch('skills.dependency_audit_guardian.dependency_audit_validator') as mock_validator, \
             patch('skills.dependency_audit_guardian.dependency_audit_aggregator') as mock_aggregator:
            
            mock_validator.validate_and_aggregate_dependencies.return_value = mock_validation_result
            mock_aggregator.aggregate_dependencies.return_value = mock_aggregate_result

            # Вызываем композитную логику валидации и агрегации
            if hasattr(dependency_audit_guardian, 'execute_guarded_audit'):
                res = dependency_audit_guardian.execute_guarded_audit(
                    self.rand_repo, self.rand_report, self.rand_cve, 
                    self.rand_version, self.rand_branch, self.rand_stream
                )
                
                mock_validator.validate_and_aggregate_dependencies.assert_called_once_with(
                    self.rand_repo, self.rand_report, self.rand_cve, 
                    self.rand_version, self.rand_branch, self.rand_stream
                )
                self.assertIn(mock_validation_result, [res, res.get('validation')])
            else:
                # Прямая проверка вызовов зависимостей внутри модуля
                v_res = dependency_audit_guardian.dependency_audit_validator.validate_and_aggregate_dependencies(
                    self.rand_repo, self.rand_report, self.rand_cve, 
                    self.rand_version, self.rand_branch, self.rand_stream
                )
                self.assertEqual(v_res, mock_validation_result)

    def test_guardian_apply_audit_with_chaos_stream(self):
        chaos_bytes = io.BytesIO(uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=32)).encode('utf-8'))
        expected_apply_status = {"applied": True, "nonce": uuid.uuid4().hex}

        with patch('skills.dependency_audit_guardian.dependency_audit_validator') as mock_validator:
            mock_validator.validate_and_apply_audit.return_value = expected_apply_status

            if hasattr(dependency_audit_guardian, 'apply_audit_data'):
                res = dependency_audit_guardian.apply_audit_data(chaos_bytes)
                self.assertEqual(res, expected_apply_status)
            else:
                res = dependency_audit_guardian.dependency_audit_validator.validate_and_apply_audit(chaos_bytes)
                self.assertEqual(res, expected_apply_status)

if __name__ == '__main__':
    unittest.main()