import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.release_changelog_builder import changelog_generator

class TestReleaseChangelogBuilder(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex[:8]
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_commit_hash = uuid.uuid4().hex
        self.random_author = f"User_{uuid.uuid4().hex[:6]}"
        self.random_message = f"feat({self.random_prefix}): implement strict testing rules"

    def test_changelog_generator_success(self):
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.hexsha = self.random_commit_hash
        mock_commit.author.name = self.random_author
        mock_commit.message = self.random_message
        
        mock_repo.iter_commits.return_value = [mock_commit]

        with patch('skills.release_changelog_builder.Repo', return_value=mock_repo):
            generator = changelog_generator()
            result = generator.generate(version=self.random_version)

            self.assertIn(self.random_version, result)
            self.assertIn(self.random_commit_hash[:7], result)
            self.assertIn(self.random_author, result)
            self.assertIn(self.random_message, result)

    def test_changelog_generator_empty_repo(self):
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = []

        with patch('skills.release_changelog_builder.Repo', return_value=mock_repo):
            generator = changelog_generator()
            result = generator.generate(version=self.random_version)

            self.assertIn(self.random_version, result)
            self.assertNotIn(self.random_commit_hash, result)

    def test_changelog_generator_file_output(self):
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.hexsha = self.random_commit_hash
        mock_commit.author.name = self.random_author
        mock_commit.message = self.random_message
        mock_repo.iter_commits.return_value = [mock_commit]

        random_file_path = f"/tmp/{uuid.uuid4().hex}.md"
        mock_file = MagicMock()

        with patch('skills.release_changelog_builder.Repo', return_value=mock_repo), \
             patch('builtins.open', new_callable=unittest.mock.mock_open) as mocked_file:
            
            generator = changelog_generator()
            generator.save_to_file(path=random_file_path, version=self.random_version)

            mocked_file.assert_called_once_with(random_file_path, 'w', encoding='utf-8')
            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            
            self.assertIn(self.random_version, written_data)
            self.assertIn(self.random_message, written_data)

    def test_changelog_generator_stream_parsing(self):
        random_payload = f"commit {self.random_commit_hash}\nAuthor: {self.random_author}\n\n    {self.random_message}\n".encode('utf-8')
        fake_stream = io.BytesIO(random_payload)

        generator = changelog_generator()
        parsed_entries = generator.parse_stream(fake_stream)

        self.assertEqual(len(parsed_entries), 1)
        self.assertEqual(parsed_entries[0]['hash'], self.random_commit_hash)
        self.assertEqual(parsed_entries[0]['author'], self.random_author)
        self.assertEqual(parsed_entries[0]['message'], self.random_message)

    def test_changelog_generator_categorization(self):
        types = ['feat', 'fix', 'chore', 'docs']
        chosen_type = random.choice(types)
        unique_scope = uuid.uuid4().hex[:4]
        unique_desc = uuid.uuid4().hex[:10]
        msg = f"{chosen_type}({unique_scope}): {unique_desc}"

        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.hexsha = self.random_commit_hash
        mock_commit.author.name = self.random_author
        mock_commit.message = msg
        mock_repo.iter_commits.return_value = [mock_commit]

        with patch('skills.release_changelog_builder.Repo', return_value=mock_repo):
            generator = changelog_generator()
            result = generator.generate(version=self.random_version)

            self.assertIn(chosen_type.capitalize(), result)
            self.assertIn(unique_desc, result)
            self.assertIn(unique_scope, result)

if __name__ == '__main__':
    unittest.main()