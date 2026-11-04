import unittest
import os
import uuid
from skills.repo_sync import RepoSync, start_new, RepoMonitor, RepoAutoCommitter, RepoReporter, RepoLogger

class TestRepoSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"./test_repo_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.report_filename = f"report_{uuid.uuid4().hex}.txt"
        self.report_path = os.path.join(self.test_dir, self.report_filename)

    def tearDown(self):
        if os.path.exists(self.report_path):
            os.remove(self.report_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_repo_sync_full_workflow(self):
        random_event = uuid.uuid4().hex
        random_summary = f"Summary data {uuid.uuid4().hex}"

        monitor = RepoMonitor(self.test_dir)
        status = monitor.check_status()
        self.assertIsInstance(status, str)
        self.assertTrue(len(status) > 0)

        committer = RepoAutoCommitter(self.test_dir)
        commit_result = committer.run()
        self.assertTrue(commit_result)

        process_result = committer.process_and_commit()
        self.assertTrue(process_result)

        reporter = RepoReporter(self.test_dir)
        final_report = reporter.generate_final_report()
        self.assertIsInstance(final_report, str)

        save_result = reporter.save_report(self.report_path, random_summary)
        self.assertTrue(save_result)
        self.assertTrue(os.path.exists(self.report_path))

        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, random_summary)

        logger = RepoLogger(self.test_dir)
        log_result = logger.log_event(random_event, {"identifier": uuid.uuid4().hex})
        self.assertTrue(log_result)

        syncer = RepoSync(self.test_dir)
        sync_result = syncer.synchronize()
        self.assertTrue(sync_result)

        start_result = start_new(self.test_dir)
        self.assertIsInstance(start_result, dict)
        self.assertIn("status", start_result)
        self.assertIn("report", start_result)

if __name__ == "__main__":
    unittest.main()