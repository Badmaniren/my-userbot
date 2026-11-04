import unittest
import os
import uuid
import tempfile
from skills.release_notes_publisher import ReleaseNotesPublisher

class TestReleaseNotesPublisherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.publisher = ReleaseNotesPublisher(self.repo_path)
        
        self.random_suffix = uuid.uuid4().hex[:8]
        self.output_filename = f"release_notes_{self.random_suffix}.md"
        self.output_path = os.path.join(self.repo_path, self.output_filename)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_publish_integration(self):
        result = self.publisher.publish(self.output_path)
        self.assertIsInstance(result, bool)

    def test_generate_and_notify_integration(self):
        result = self.publisher.generate_and_notify(self.output_path)
        self.assertIsInstance(result, bool)

    def test_compose_and_notify_integration(self):
        result = self.publisher.compose_and_notify(self.output_path)
        self.assertIsInstance(result, bool)

    def test_run_integration(self):
        result = self.publisher.run()
        self.assertIsInstance(result, bool)

if __name__ == '__main__':
    unittest.main()