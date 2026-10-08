import unittest
import os
import sys
import json
import tempfile
from unittest.mock import patch

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    from market_portfolio_stress_audit_exporter_v2 import (
        StressAuditExporterV2,
        AntiCheatSecurityGuard,
        StressTelemetryException
    )
except ImportError:
    from skills.market_portfolio_stress_audit_exporter_v2 import (
        StressAuditExporterV2,
        AntiCheatSecurityGuard,
        StressTelemetryException
    )

class TestStressAuditTelemetryRealConditions(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file_path = os.path.join(self.test_dir.name, "stress_audit_telemetry_live.json")

        self.raw_telemetry_records = [
            {"timestamp": "2023-10-27T10:00:00Z", "portfolio_id": "PORT-001", "var_99": 125000.50, "stress_drawdown_pct": -22.4, "status": "CRITICAL_BREACH", "anti_cheat_hash": "valid_hash_01"},
            {"timestamp": "2023-10-27T10:05:00Z", "portfolio_id": "PORT-001", "var_99": 118000.00, "stress_drawdown_pct": -19.1, "status": "WARNING", "anti_cheat_hash": "valid_hash_02"},
            {"timestamp": "2023-10-27T10:10:00Z", "portfolio_id": "PORT-002", "var_99": 45000.20, "stress_drawdown_pct": -8.5, "status": "STABLE", "anti_cheat_hash": "valid_hash_03"},
            {"timestamp": "2023-10-27T10:15:00Z", "portfolio_id": "PORT-003", "var_99": 310000.00, "stress_drawdown_pct": -35.2, "status": "CRITICAL_BREACH", "anti_cheat_hash": "valid_hash_04"},
            {"timestamp": "2023-10-27T10:20:00Z", "portfolio_id": "PORT-002", "var_99": 42100.00, "stress_drawdown_pct": -7.9, "status": "STABLE", "anti_cheat_hash": "valid_hash_05"},
            {"timestamp": "2023-10-27T10:25:00Z", "portfolio_id": "PORT-001", "var_99": 130200.75, "stress_drawdown_pct": -24.8, "status": "CRITICAL_BREACH", "anti_cheat_hash": "valid_hash_06"},
            {"timestamp": "2023-10-27T10:30:00Z", "portfolio_id": "PORT-004", "var_99": 15000.00, "stress_drawdown_pct": -3.1, "status": "STABLE", "anti_cheat_hash": "valid_hash_07"},
            {"timestamp": "2023-10-27T10:35:00Z", "portfolio_id": "PORT-003", "var_99": 295000.10, "stress_drawdown_pct": -31.0, "status": "CRITICAL_BREACH", "anti_cheat_hash": "valid_hash_08"},
            {"timestamp": "2023-10-27T10:40:00Z", "portfolio_id": "PORT-002", "var_99": 44000.00, "stress_drawdown_pct": -8.2, "status": "STABLE", "anti_cheat_hash": "valid_hash_09"},
            {"timestamp": "2023-10-27T10:45:00Z", "portfolio_id": "PORT-001", "var_99": 121000.00, "stress_drawdown_pct": -20.5, "status": "WARNING", "anti_cheat_hash": "valid_hash_10"},
            {"timestamp": "2023-10-27T10:50:00Z", "portfolio_id": "PORT-005", "var_99": 550000.00, "stress_drawdown_pct": -45.0, "status": "CRITICAL_BREACH", "anti_cheat_hash": "valid_hash_11"},
            {"timestamp": "2023-10-27T10:55:00Z", "portfolio_id": "PORT-004", "var_99": 15500.00, "stress_drawdown_pct": -3.3, "status": "STABLE", "anti_cheat_hash": "valid_hash_12"},
            {"timestamp": "2023-10-27T11:00:00Z", "portfolio_id": "PORT-003", "var_99": 280000.00, "stress_drawdown_pct": -29.8, "status": "CRITICAL_BREACH", "anti_cheat_hash": "valid_hash_13"},
            {"timestamp": "2023-10-27T11:05:00Z", "portfolio_id": "PORT-002", "var_99": 43000.00, "stress_drawdown_pct": -8.0, "status": "STABLE", "anti_cheat_hash": "valid_hash_14"},
            {"timestamp": "2023-10-27T11:10:00Z", "portfolio_id": "PORT-001", "var_99": 119000.00, "stress_drawdown_pct": -19.8, "status": "WARNING", "anti_cheat_hash": "valid_hash_15"},
            {"timestamp": "2023-10-27T11:15:00Z", "portfolio_id": "PORT-005", "var_99": 540000.00, "stress_drawdown_pct": -44.2, "status": "CRITICAL_BREACH", "anti_cheat_hash": "valid_hash_16"},
            {"timestamp": "2023-10-27T11:20:00Z", "portfolio_id": "PORT-004", "var_99": 15200.00, "stress_drawdown_pct": -3.2, "status": "STABLE", "anti_cheat_hash": "valid_hash_17"},
            {"timestamp": "2023-10-27T11:25:00Z", "portfolio_id": "PORT-003", "var_99": 285000.00, "stress_drawdown_pct": -30.1, "status": "CRITICAL_BREACH", "anti_cheat_hash": "valid_hash_18"},
            {"timestamp": "2023-10-27T11:30:00Z", "portfolio_id": "PORT-002", "var_99": 43500.00, "stress_drawdown_pct": -8.1, "status": "STABLE", "anti_cheat_hash": "valid_hash_19"},
            {"timestamp": "2023-10-27T11:35:00Z", "portfolio_id": "PORT-001", "var_99": 122000.00, "stress_drawdown_pct": -21.0, "status": "WARNING", "anti_cheat_hash": "valid_hash_20"},
            {"timestamp": "2023-10-27T11:40:00Z", "portfolio_id": "PORT-005", "var_99": 560000.00, "stress_drawdown_pct": -46.5, "status": "CRITICAL_BREACH", "anti_cheat_hash": "tampered_hash_bad"}
        ]

        with open(self.log_file_path, "w", encoding="utf-8") as f:
            json.dump(self.raw_telemetry_records, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_audit_exporter_v2_real_pipeline(self):
        print("\n=== STARTING PRACTICAL VERIFICATION: market_portfolio_stress_audit_exporter_v2 ===")
        print(f"Temporary telemetry dataset created at: {self.log_file_path}")
        print(f"Total raw telemetry records loaded: {len(self.raw_telemetry_records)}")

        exporter = StressAuditExporterV2(storage_path=self.log_file_path)

        parsed_data = exporter.load_telemetry_stream()
        print(f"Exporter successfully read {len(parsed_data)} records from storage.")

        anti_cheat = AntiCheatSecurityGuard()
        verified_records = []
        tampered_count = 0

        for record in parsed_data:
            is_valid = anti_cheat.verify_record_integrity(record)
            if is_valid:
                verified_records.append(record)
            else:
                tampered_count += 1
                print(f"[ANTI-CHEAT ALERT] Tampered or corrupted telemetry detected for portfolio: {record.get('portfolio_id')} at {record.get('timestamp')}")

        print(f"Anti-cheat verification completed. Valid records: {len(verified_records)}, Rejected/Tampered records: {tampered_count}")

        self.assertEqual(tampered_count, 1, "Expected exactly 1 tampered record to be caught by the anti-cheat guard.")
        self.assertEqual(len(verified_records), 20, "Expected 20 valid records to pass verification.")

        summary_metrics = exporter.compute_stress_audit_summary(verified_records)
        print("\n--- STRESS AUDIT SUMMARY METRICS ---")
        print(json.dumps(summary_metrics, indent=2))

        self.assertIn("total_audited", summary_metrics)
        self.assertIn("critical_breaches_count", summary_metrics)
        self.assertEqual(summary_metrics["total_audited"], 20)

        critical_count = sum(1 for r in verified_records if r["status"] == "CRITICAL_BREACH")
        self.assertEqual(summary_metrics["critical_breaches_count"], critical_count)
        print(f"Verified critical breaches count matches summary: {critical_count}")

        export_result = exporter.export_final_telemetry_bundle(verified_records)
        print(f"Final telemetry bundle export status: {export_result.get('status')}")
        print(f"Export destination checksum: {export_result.get('checksum')}")

        self.assertEqual(export_result.get("status"), "SUCCESS")
        print("=== PRACTICAL VERIFICATION PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    unittest.main()
