import unittest
from unittest.mock import patch
import io
import json
import hashlib
import random
import uuid
from skills.market_portfolio_audit_chain_validator import AuditChainValidator, validate_audit_chain


class TestMarketPortfolioAuditChainValidator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.stream_id = uuid.uuid4().hex
        self.table_name = uuid.uuid4().hex
        self.url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"

    @patch("skills.market_portfolio_audit_chain_validator.get_audit_logs_by_portfolio")
    def test_validate_chain_empty_logs(self, mock_get_logs):
        mock_get_logs.return_value = []
        validator = AuditChainValidator()
        result = validator.validate_chain(self.table_name)
        self.assertTrue(result)
        mock_get_logs.assert_called_once_with(self.table_name)

    def test_validate_chain_with_storage_empty_logs(self):
        mock_storage = unittest.mock.MagicMock()
        mock_storage.fetch_logs.return_value = []
        validator = AuditChainValidator(db_storage=mock_storage)
        result = validator.validate_chain(self.table_name)
        self.assertTrue(result)
        mock_storage.fetch_logs.assert_called_once_with(self.table_name)

    def test_validate_chain_success(self):
        record_id = uuid.uuid4().hex
        payload = uuid.uuid4().hex
        prev_hash = "0" * 64
        raw_str = f"{prev_hash}:{record_id}:{payload}"
        current_hash = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

        logs = [
            {
                "id": record_id,
                "payload": payload,
                "prev_hash": prev_hash,
                "hash": current_hash
            }
        ]

        mock_storage = unittest.mock.MagicMock()
        mock_storage.fetch_logs.return_value = logs
        validator = AuditChainValidator(db_storage=mock_storage)
        self.assertTrue(validator.validate_chain(self.table_name))

    def test_validate_chain_invalid_first_prev_hash(self):
        record_id = uuid.uuid4().hex
        payload = uuid.uuid4().hex
        bad_prev_hash = uuid.uuid4().hex
        logs = [
            {
                "id": record_id,
                "payload": payload,
                "prev_hash": bad_prev_hash,
                "hash": uuid.uuid4().hex
            }
        ]

        mock_storage = unittest.mock.MagicMock()
        mock_storage.fetch_logs.return_value = logs
        validator = AuditChainValidator(db_storage=mock_storage)

        with self.assertRaises(ValueError):
            validator.validate_chain(self.table_name)

    def test_validate_chain_broken_hash_chain(self):
        record_id_1 = uuid.uuid4().hex
        payload_1 = uuid.uuid4().hex
        hash_1 = uuid.uuid4().hex

        record_id_2 = uuid.uuid4().hex
        payload_2 = uuid.uuid4().hex

        logs = [
            {
                "id": record_id_1,
                "payload": payload_1,
                "prev_hash": "0" * 64,
                "hash": hash_1
            },
            {
                "id": record_id_2,
                "payload": payload_2,
                "prev_hash": uuid.uuid4().hex,
                "hash": uuid.uuid4().hex
            }
        ]

        mock_storage = unittest.mock.MagicMock()
        mock_storage.fetch_logs.return_value = logs
        validator = AuditChainValidator(db_storage=mock_storage)

        with self.assertRaises(ValueError):
            validator.validate_chain(self.table_name)

    def test_validate_chain_hash_mismatch(self):
        record_id = uuid.uuid4().hex
        payload = uuid.uuid4().hex
        prev_hash = "0" * 64
        fake_hash = uuid.uuid4().hex

        logs = [
            {
                "id": record_id,
                "payload": payload,
                "prev_hash": prev_hash,
                "hash": fake_hash
            }
        ]

        mock_storage = unittest.mock.MagicMock()
        mock_storage.fetch_logs.return_value = logs
        validator = AuditChainValidator(db_storage=mock_storage)

        with self.assertRaises(ValueError):
            validator.validate_chain(self.table_name)

    def test_verify_sequence_empty(self):
        mock_storage = unittest.mock.MagicMock()
        mock_storage.fetch_stream.return_value = []
        validator = AuditChainValidator(db_storage=mock_storage)
        self.assertTrue(validator.verify_sequence(self.stream_id))

    def test_verify_sequence_success(self):
        start_seq = random.randint(1, 1000)
        logs = [
            {"sequence": start_seq},
            {"sequence": start_seq + 1},
            {"sequence": start_seq + 2}
        ]

        mock_storage = unittest.mock.MagicMock()
        mock_storage.fetch_stream.return_value = logs
        validator = AuditChainValidator(db_storage=mock_storage)
        self.assertTrue(validator.verify_sequence(self.stream_id))

    def test_verify_sequence_discontinuity(self):
        start_seq = random.randint(1, 1000)
        logs = [
            {"sequence": start_seq},
            {"sequence": start_seq + 5}
        ]

        mock_storage = unittest.mock.MagicMock()
        mock_storage.fetch_stream.return_value = logs
        validator = AuditChainValidator(db_storage=mock_storage)

        with self.assertRaises(RuntimeError):
            validator.verify_sequence(self.stream_id)

    def test_extract_and_verify_stream_token(self):
        expected_token = uuid.uuid4().hex
        response_data = json.dumps({"token": expected_token}).encode('utf-8')

        mock_response = unittest.mock.MagicMock()
        mock_response.raw = io.BytesIO(response_data)

        with patch("requests.get", return_value=mock_response) as mock_get:
            validator = AuditChainValidator()
            token = validator.extract_and_verify_stream_token(self.url)
            self.assertEqual(token, expected_token)
            mock_get.assert_called_once_with(self.url)


class TestMarketPortfolioAuditChainValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex

    @patch("skills.market_portfolio_audit_chain_validator.get_audit_logs_by_portfolio")
    def test_validate_audit_chain_empty(self, mock_get_logs):
        mock_get_logs.return_value = []
        res = validate_audit_chain(self.portfolio_id)
        self.assertEqual(res, {"is_valid": True})
        mock_get_logs.assert_called_once_with(self.portfolio_id)

    @patch("skills.market_portfolio_audit_chain_validator.get_audit_logs_by_portfolio")
    def test_validate_audit_chain_valid_sequence(self, mock_get_logs):
        hash_1 = uuid.uuid4().hex
        hash_2 = uuid.uuid4().hex

        logs = [
            {"hash": hash_1},
            {"previous_hash": hash_1, "hash": hash_2},
            {"previous_hash": hash_2, "hash": uuid.uuid4().hex}
        ]
        mock_get_logs.return_value = logs

        res = validate_audit_chain(self.portfolio_id)
        self.assertTrue(res["is_valid"])
        self.assertIsNone(res["broken_index"])

    @patch("skills.market_portfolio_audit_chain_validator.get_audit_logs_by_portfolio")
    def test_validate_audit_chain_broken_sequence(self, mock_get_logs):
        hash_1 = uuid.uuid4().hex
        wrong_hash = uuid.uuid4().hex

        logs = [
            {"hash": hash_1},
            {"previous_hash": wrong_hash, "hash": uuid.uuid4().hex}
        ]
        mock_get_logs.return_value = logs

        res = validate_audit_chain(self.portfolio_id)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["broken_index"], 1)