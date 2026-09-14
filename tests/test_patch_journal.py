import os
import tempfile
import unittest
import json
import uuid
import random
import io
from unittest.mock import patch

from skills.patch_journal import JournalEntry, PatchJournal, JournalStreamVerifier

class TestPatchJournal(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.rand_filename = f"{uuid.uuid4().hex}.jsonl"
        self.storage_path = os.path.join(self.temp_dir.name, self.rand_filename)
        self.journal = PatchJournal(storage_path=self.storage_path)
        self.verifier = JournalStreamVerifier()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_journal_entry_to_dict(self):
        success = random.choice([True, False])
        incident_id = uuid.uuid4().hex
        module_name = f"mod_{uuid.uuid4().hex[:6]}"
        error = f"err_{uuid.uuid4().hex[:6]}"
        patch_data = f"patch_{uuid.uuid4().hex[:6]}"
        timestamp = random.random() * 1000000

        entry = JournalEntry(
            success=success,
            incident_id=incident_id,
            module_name=module_name,
            error=error,
            patch_data=patch_data,
            timestamp=timestamp
        )

        d = entry.to_dict()
        self.assertEqual(d["success"], success)
        self.assertEqual(d["incident_id"], incident_id)
        self.assertEqual(d["module_name"], module_name)
        self.assertEqual(d["error"], error)
        self.assertEqual(d["patch_data"], patch_data)
        self.assertEqual(d["timestamp"], timestamp)

    def test_log_event_and_get_all(self):
        success = True
        incident_id = uuid.uuid4().hex
        module_name = f"module_{uuid.uuid4().hex[:8]}"
        error = f"error_{uuid.uuid4().hex[:8]}"
        patch_data = f"code_{uuid.uuid4().hex[:8]}"

        self.journal.log_event(
            success=success,
            incident_id=incident_id,
            module_name=module_name,
            error=error,
            patch_data=patch_data
        )

        records = self.journal.get_all()
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec["incident_id"], incident_id)
        self.assertEqual(rec["module_name"], module_name)
        self.assertEqual(rec["error"], error)
        self.assertEqual(rec["patch_data"], patch_data)
        self.assertIsInstance(rec["timestamp"], float)

    def test_get_records_by_module_name(self):
        mod_target = f"target_{uuid.uuid4().hex[:6]}"
        mod_other = f"other_{uuid.uuid4().hex[:6]}"

        inc_1 = uuid.uuid4().hex
        inc_2 = uuid.uuid4().hex
        inc_3 = uuid.uuid4().hex

        self.journal.log_event(True, inc_1, mod_target, "err1", "patch1")
        self.journal.log_event(False, inc_2, mod_other, "err2", "patch2")
        self.journal.log_event(True, inc_3, mod_target, "err3", "patch3")

        target_records = self.journal.get_records(module_name=mod_target)
        self.assertEqual(len(target_records), 2)
        for r in target_records:
            self.assertEqual(r["module_name"], mod_target)

        all_records = self.journal.get_records(module_name=None)
        self.assertEqual(len(all_records), 3)

    def test_get_history(self):
        mod_name = f"hist_{uuid.uuid4().hex[:6]}"
        inc_id = uuid.uuid4().hex
        self.journal.log_event(True, inc_id, mod_name, "some_err", "some_patch")

        history = self.journal.get_history(module_name=mod_name)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["module_name"], mod_name)
        self.assertEqual(history[0]["incident_id"], inc_id)

    def test_get_incident_logs(self):
        target_inc = uuid.uuid4().hex
        other_inc = uuid.uuid4().hex
        mod_name = f"mod_{uuid.uuid4().hex[:6]}"

        self.journal.log_event(False, other_inc, mod_name, "err_other", "patch_other")
        self.journal.log_event(True, target_inc, mod_name, "err_target", "patch_target")

        log_entry = self.journal.get_incident_logs(incident_id=target_inc)
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry["incident_id"], target_inc)
        self.assertEqual(log_entry["error"], "err_target")

        missing_entry = self.journal.get_incident_logs(incident_id=uuid.uuid4().hex)
        self.assertIsNone(missing_entry)

    def test_get_all_with_corrupted_json(self):
        valid_inc = uuid.uuid4().hex
        mod_name = f"mod_{uuid.uuid4().hex[:6]}"
        self.journal.log_event(True, valid_inc, mod_name, "err", "patch")

        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write("THIS IS NOT VALID JSON\n")

        valid_inc_2 = uuid.uuid4().hex
        self.journal.log_event(False, valid_inc_2, mod_name, "err2", "patch2")

        records = self.journal.get_all()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["incident_id"], valid_inc)
        self.assertEqual(records[1]["incident_id"], valid_inc_2)

    def test_get_all_missing_file(self):
        non_existent_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.jsonl")
        j = PatchJournal(storage_path=non_existent_path)
        self.assertEqual(j.get_all(), [])

    def verify_stream_with_bytes_io(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_bytes)
        res = self.verifier.verify_stream(stream)
        self.assertTrue(res["valid"])
        self.assertEqual(res["size"], len(random_bytes))

    def verify_stream_with_list_and_dict(self):
        data_list = [uuid.uuid4().hex, random.randint(1, 100)]
        res_list = self.verifier.verify_stream(data_list)
        self.assertTrue(res_list["valid"])
        self.assertGreater(res_list["size"], 0)

        data_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        res_dict = self.verifier.verify_stream(data_dict)
        self.assertTrue(res_dict["valid"])
        self.assertGreater(res_dict["size"], 0)

    def verify_stream_with_arbitrary_object(self):
        rand_str = uuid.uuid4().hex
        res = self.verifier.verify_stream(rand_str)
        self.assertTrue(res["valid"])
        self.assertEqual(res["size"], len(rand_str.encode('utf-8')))

    def test_verify_stream_variants(self):
        self.verify_stream_with_bytes_io()
        self.verify_stream_with_list_and_dict()
        self.verify_stream_with_arbitrary_object()