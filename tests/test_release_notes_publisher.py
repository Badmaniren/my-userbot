import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.release_notes_publisher import ReleaseNotesPublisher

class TestReleaseNotesPublisher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.output_path = f"/tmp/{uuid.uuid4().hex}.md"
        self.publisher = ReleaseNotesPublisher(self.repo_path)

    def test_init_sets_repo_path(self):
        random_path = f"/var/repo/{uuid.uuid4().hex}"
        publisher = ReleaseNotesPublisher(random_path)
        self.assertEqual(publisher.repo_path, random_path)

    @patch('skills.release_notes_publisher.ReleaseNotesComposer')
    @patch('skills.release_notes_publisher.RepoNotifier')
    def test_publish_success_flow(self, mock_notifier_class, mock_composer_class):
        mock_composer_instance = mock_composer_class.return_value
        expected_notes = f"Release Notes: {uuid.uuid4().hex}"
        mock_composer_instance.compose.return_value = expected_notes
        mock_composer_instance.generate.return_value = expected_notes
        mock_composer_instance.run.return_value = expected_notes

        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify.return_value = True
        mock_notifier_instance.notify_and_commit.return_value = True

        result = self.publisher.publish(self.output_path)

        mock_composer_class.assert_called_once_with(self.repo_path)
        mock_composer_instance.compose.assert_called_once_with(self.output_path)
        mock_notifier_class.assert_called_once_with(self.repo_path)
        mock_notifier_instance.notify.assert_called_once_with(self.output_path)
        self.assertTrue(result)

    @patch('skills.release_notes_publisher.ReleaseNotesComposer')
    @patch('skills.release_notes_publisher.RepoNotifier')
    def test_publish_composer_fails(self, mock_notifier_class, mock_composer_class):
        mock_composer_instance = mock_composer_class.return_value
        mock_composer_instance.compose.side_effect = Exception(uuid.uuid4().hex)

        mock_notifier_instance = mock_notifier_class.return_value

        with self.assertRaises(Exception):
            self.publisher.publish(self.output_path)

        mock_notifier_instance.notify.assert_not_called()

    @patch('skills.release_notes_publisher.ReleaseNotesComposer')
    @patch('skills.release_notes_publisher.RepoNotifier')
    def test_publish_notifier_fails(self, mock_notifier_class, mock_composer_class):
        mock_composer_instance = mock_composer_class.return_value
        mock_composer_instance.compose.return_value = uuid.uuid4().hex

        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify.return_value = False

        result = self.publisher.publish(self.output_path)

        self.assertFalse(result)

    @patch('skills.release_notes_publisher.ReleaseNotesComposer')
    @patch('skills.release_notes_publisher.RepoNotifier')
    def test_run_digest_distribution(self, mock_notifier_class, mock_composer_class):
        mock_composer_instance = mock_composer_class.return_value
        mock_composer_instance.run.return_value = uuid.uuid4().hex

        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify_and_commit.return_value = True

        result = self.publisher.run()

        mock_composer_class.assert_called_once_with(self.repo_path)
        mock_composer_instance.run.assert_called_once()
        mock_notifier_class.assert_called_once_with(self.repo_path)
        mock_notifier_instance.notify_and_commit.assert_called_once()
        self.assertTrue(result)

    @patch('skills.release_notes_publisher.ReleaseNotesComposer')
    @patch('skills.release_notes_publisher.RepoNotifier')
    def test_custom_generation_and_notification(self, mock_notifier_class, mock_composer_class):
        custom_output = f"/home/user/{uuid.uuid4().hex}.txt"
        mock_composer_instance = mock_composer_class.return_value
        mock_composer_instance.generate.return_value = uuid.uuid4().hex

        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify.return_value = True

        res = self.publisher.generate_and_notify(custom_output)

        mock_composer_instance.generate.assert_called_once_with(custom_output)
        mock_notifier_instance.notify.assert_called_once_with(custom_output)
        self.assertTrue(res)

if __name__ == '__main__':
    unittest.main()