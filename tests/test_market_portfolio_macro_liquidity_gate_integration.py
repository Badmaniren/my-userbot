import unittest
import uuid
import random
import time
from skills.market_portfolio_macro_liquidity_gate import MacroLiquidityGate, check_macro_liquidity_availability
from skills.db_storage import save_audit_record, fetch_audit_record

class TestMacroLiquidityGateIntegration(unittest.TestCase):
    def test_macro_liquidity_gate_real_flow(self):
        unique_endpoint = f"https://httpbin.org/anything/{uuid.uuid4()}"
        timeout_val = random.randint(3, 7)

        gate = MacroLiquidityGate(macro_endpoint=unique_endpoint, timeout=timeout_val)
        self.assertEqual(gate.macro_endpoint, unique_endpoint)
        self.assertEqual(gate.timeout, timeout_val)

        liquidity_result = gate.check_liquidity()
        self.assertIn("available", liquidity_result)
        self.assertIn("liquidity_index", liquidity_result)

        random_index = round(random.uniform(10.0, 1000.0), 4)
        random_status = f"status_{uuid.uuid4().hex[:8]}"
        payload = {
            "liquidity_index": random_index,
            "status": random_status,
            "test_id": str(uuid.uuid4())
        }

        availability_result = check_macro_liquidity_availability(payload)
        self.assertTrue(availability_result["available"])
        self.assertEqual(availability_result["liquidity_index"], random_index)
        self.assertEqual(availability_result["status"], random_status)
        self.assertEqual(availability_result["test_id"], payload["test_id"])
        self.assertIn("timestamp", availability_result)

        audit_key = f"macro_audit_{uuid.uuid4().hex}"
        audit_data = {
            "endpoint": unique_endpoint,
            "payload": payload,
            "result": availability_result,
            "random_metric": random.randint(1, 100000)
        }

        save_audit_record(audit_key, audit_data)
        fetched_record = fetch_audit_record(audit_key)

        self.assertIsNotNone(fetched_record)
        self.assertEqual(fetched_record.get("endpoint"), unique_endpoint)
        self.assertEqual(fetched_record.get("payload", {}).get("test_id"), payload["test_id"])
        self.assertEqual(fetched_record.get("random_metric"), audit_data["random_metric"])

if __name__ == "__main__":
    unittest.main()