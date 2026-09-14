import unittest
import os
import tempfile
import uuid
import random
from skills.patch_journal import PatchJournal, JournalEntry, JournalStreamVerifier
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.auto_patch_pipeline import AutoPatchPipeline

class TestPatchJournalIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_path = os.path.join(self.test_dir.name, f"journal_{uuid.uuid4()}.jsonl")
        self.journal = PatchJournal(storage_path=self.storage_path)
        self.verifier = JournalStreamVerifier()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_journal_and_pipeline_integration(self):
        incident_id = str(uuid.uuid4())
        module_name = f"module_{uuid.uuid4().hex[:6]}"
        error_msg = f"RuntimeError: simulated failure {random.randint(1000, 9999)}"
        patch_code = f"def fixed_{random.randint(1, 100)}(): pass"
        success_status = random.choice([True, False])

        self.journal.log_event(
            success=success_status,
            incident_id=incident_id,
            module_name=module_name,
            error=error_msg,
            patch_data=patch_code
        )

        self.assertTrue(os.path.exists(self.storage_path), "Файл журнала не был создан на диске.")

        all_records = self.journal.get_all()
        self.assertEqual(len(all_records), 1, "Количество записей в журнале не совпадает с ожидаемым.")

        record = all_records[0]
        self.assertEqual(record.get("incident_id"), incident_id)
        self.assertEqual(record.get("module_name"), module_name)
        self.assertEqual(record.get("error"), error_msg)
        self.assertEqual(record.get("patch_data"), patch_code)
        self.assertEqual(record.get("success"), success_status)

        history = self.journal.get_history(module_name)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].get("incident_id"), incident_id)

        logged_entry = self.journal.get_incident_logs(incident_id)
        self.assertIsNotNone(logged_entry)
        self.assertEqual(logged_entry.get("error"), error_msg)

        stream_result = self.verifier.verify_stream(patch_code)
        self.assertTrue(stream_result.get("valid"))
        self.assertGreater(stream_result.get("size"), 0)

        hub = ErrorRecoveryHub()
        captured = hub.capture_failure(module_name, Exception(error_msg), "Traceback info...")
        self.assertIsInstance(captured, dict)

        pipeline = AutoPatchPipeline()
        stream_verification = pipeline.verify_patch_stream(patch_code)
        self.assertTrue(stream_verification.get("valid"))

if __name__ == "__main__":
    unittest.main()