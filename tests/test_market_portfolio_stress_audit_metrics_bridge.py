import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills import db_storage
from skills.market_portfolio_stress_audit_metrics_bridge import start_new


class TestMarketPortfolioStressAuditMetricsBridge(unittest.TestCase):

    def test_start_new_success_with_commit(self):
        session_id = uuid.uuid4().hex
        metric_name = "metric_" + uuid.uuid4().hex[:8]
        value = round(random.uniform(1.0, 1000.0), 2)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.commit = MagicMock()

        with patch.object(db_storage, "get_connection", return_value=mock_conn) as get_conn_mock:
            result = start_new(session_id, metric_name, value)

            get_conn_mock.assert_called_once()
            mock_conn.cursor.assert_called_once()
            mock_cursor.execute.assert_called_once_with(
                "INSERT INTO market_portfolio_stress_audit_metrics_bridge (session_id, metric_name, value) VALUES (?, ?, ?)",
                (session_id, metric_name, value)
            )
            mock_conn.commit.assert_called_once()
            self.assertEqual(result, session_id)

    def test_start_new_success_without_commit(self):
        session_id = uuid.uuid4().hex
        metric_name = "metric_" + uuid.uuid4().hex[:8]
        value = round(random.uniform(-500.0, 500.0), 4)

        mock_conn = MagicMock(spec=[])
        mock_cursor = MagicMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor)

        with patch.object(db_storage, "get_connection", return_value=mock_conn) as get_conn_mock:
            result = start_new(session_id, metric_name, value)

            get_conn_mock.assert_called_once()
            mock_conn.cursor.assert_called_once()
            mock_cursor.execute.assert_called_once_with(
                "INSERT INTO market_portfolio_stress_audit_metrics_bridge (session_id, metric_name, value) VALUES (?, ?, ?)",
                (session_id, metric_name, value)
            )
            self.assertFalse(hasattr(mock_conn, "commit"))
            self.assertEqual(result, session_id)

    def test_start_new_database_exception_no_suppression(self):
        session_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        value = random.randint(0, 100)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = RuntimeError("Database integrity violation " + uuid.uuid4().hex)

        with patch.object(db_storage, "get_connection", return_value=mock_conn):
            with self.assertRaises(RuntimeError):
                start_new(session_id, metric_name, value)


if __name__ == "__main__":
    unittest.main()
