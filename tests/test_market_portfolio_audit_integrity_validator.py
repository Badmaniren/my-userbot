import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.market_portfolio_audit_integrity_validator import (
    MarketPortfolioAuditIntegrityValidator,
    ValidationError,
    ChecksumMismatchError
)


class TestMarketPortfolioAuditIntegrityValidator(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.validator = MarketPortfolioAuditIntegrityValidator(db_storage=self.db_storage)
        self.random_namespace = uuid.uuid4().hex

    def test_validate_and_store_success(self):
        report_id = uuid.uuid4().hex
        valid_checksum = uuid.uuid4().hex
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_price = round(random.uniform(10.0, 1500.0), 2)

        report_data = {
            "report_id": report_id,
            "symbol": random_symbol,
            "price": random_price,
            "checksum": valid_checksum
        }

        raw_payload = json.dumps(report_data).encode('utf-8')
        mock_stream = io.BytesIO(raw_payload)

        with patch('skills.market_portfolio_audit_integrity_validator.hashlib') as mock_hashlib:
            mock_sha = MagicMock()
            mock_sha.hexdigest.return_value = valid_checksum
            mock_hashlib.sha256.return_value = mock_sha

            result = self.validator.validate_and_store(mock_stream)

            self.assertTrue(result)
            self.db_storage.save.assert_called_once()
            stored_arg = self.db_storage.save.call_args[0][0]
            self.assertEqual(stored_arg["report_id"], report_id)
            self.assertEqual(stored_arg["symbol"], random_symbol)

    def test_validate_checksum_mismatch(self):
        report_id = uuid.uuid4().hex
        actual_checksum = uuid.uuid4().hex
        forged_checksum = uuid.uuid4().hex

        report_data = {
            "report_id": report_id,
            "checksum": forged_checksum
        }

        raw_payload = json.dumps(report_data).encode('utf-8')
        mock_stream = io.BytesIO(raw_payload)

        with patch('skills.market_portfolio_audit_integrity_validator.hashlib') as mock_hashlib:
            mock_sha = MagicMock()
            mock_sha.hexdigest.return_value = actual_checksum
            mock_hashlib.sha256.return_value = mock_sha

            with self.assertRaises(ChecksumMismatchError):
                self.validator.validate_and_store(mock_stream)

            self.db_storage.save.assert_not_called()

    def test_validate_schema_failure(self):
        corrupted_data = {
            "invalid_key": uuid.uuid4().hex,
            "random_val": random.randint(100, 999)
        }

        raw_payload = json.dumps(corrupted_data).encode('utf-8')
        mock_stream = io.BytesIO(raw_payload)

        valid_checksum = uuid.uuid4().hex

        with patch('skills.market_portfolio_audit_integrity_validator.hashlib') as mock_hashlib:
            mock_sha = MagicMock()
            mock_sha.hexdigest.return_value = valid_checksum
            mock_hashlib.sha256.return_value = mock_sha

            with self.assertRaises(ValidationError):
                self.validator.validate_and_store(mock_stream)

            self.db_storage.save.assert_not_called()

    def test_malformed_json_stream(self):
        random_garbage = ''.join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')
        mock_stream = io.BytesIO(random_garbage)

        with self.assertRaises(ValidationError):
            self.validator.validate_and_store(mock_stream)

        self.db_storage.save.assert_not_called()


if __name__ == '__main__':
    unittest.main()