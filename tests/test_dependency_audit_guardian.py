import unittest
from unittest.mock import patch
import uuid
import random
import io
from skills import dependency_audit_guardian

class TestDependencyAuditGuardian(unittest.TestCase):

    def test_start_new_audit_proxy(self):
        rand_repo = uuid.uuid4().hex
        rand_branch = uuid.uuid4().hex
        rand_stream = uuid.uuid4().hex
        expected_result = {'status': uuid.uuid4().hex}

        with patch('skills.dependency_audit_aggregator.start_new', return_value=expected_result) as mock_aggregator:
            res = dependency_audit_guardian.start_new(rand_repo, rand_branch, rand_stream)
            mock_aggregator.assert_called_once_with(rand_repo, rand_branch, rand_stream)
            self.assertEqual(res, expected_result)

    def test_execute_guarded_audit_proxy(self):
        rand_repo = uuid.uuid4().hex
        rand_report = uuid.uuid4().hex
        rand_cve = uuid.uuid4().hex
        rand_version = uuid.uuid4().hex
        rand_branch = uuid.uuid4().hex
        rand_stream = uuid.uuid4().hex
        expected_result = [uuid.uuid4().hex, random.randint(1, 100)]

        with patch('skills.dependency_audit_validator.validate_and_aggregate_dependencies', return_value=expected_result) as mock_validator:
            res = dependency_audit_guardian.execute_guarded_audit(
                rand_repo, rand_report, rand_cve, rand_version, rand_branch, rand_stream
            )
            mock_validator.assert_called_once_with(
                rand_repo, rand_report, rand_cve, rand_version, rand_branch, rand_stream
            )
            self.assertEqual(res, expected_result)

    def test_apply_audit_data_proxy(self):
        rand_bytes = io.BytesIO(uuid.uuid4().bytes).read()
        expected_result = random.choice([True, False])

        with patch('skills.dependency_audit_validator.validate_and_apply_audit', return_value=expected_result) as mock_validator:
            res = dependency_audit_guardian.apply_audit_data(rand_bytes)
            mock_validator.assert_called_once_with(rand_bytes)
            self.assertEqual(res, expected_result)

    def test_validate_and_aggregate_dependencies_proxy(self):
        rand_repo = uuid.uuid4().hex
        rand_report = uuid.uuid4().hex
        rand_cve = uuid.uuid4().hex
        rand_version = uuid.uuid4().hex
        rand_branch = uuid.uuid4().hex
        rand_stream = uuid.uuid4().hex
        expected_result = uuid.uuid4().hex

        with patch('skills.dependency_audit_validator.validate_and_aggregate_dependencies', return_value=expected_result) as mock_validator:
            res = dependency_audit_guardian.validate_and_aggregate_dependencies(
                rand_repo, rand_report, rand_cve, rand_version, rand_branch, rand_stream
            )
            mock_validator.assert_called_once_with(
                rand_repo, rand_report, rand_cve, rand_version, rand_branch, rand_stream
            )
            self.assertEqual(res, expected_result)

if __name__ == '__main__':
    unittest.main()