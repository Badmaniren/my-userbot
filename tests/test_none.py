import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import json
import os
from skills.none import start_new, epic_completion_proposal_handler

class TestNoneSkill(unittest.TestCase):

    def test_start_new_success(self):
        epic_id = f"epic-{uuid.uuid4().hex}"
        proposal = f"proposal-{uuid.uuid4().hex}"
        expected_response = {"status": "success", "direction_id": f"dir-{uuid.uuid4().hex}"}

        with patch("skills.none.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = expected_response

            result = start_new(epic_id, proposal)

            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_kwargs["json"]["epic_id"], epic_id)
            self.assertEqual(called_kwargs["json"]["proposal"], proposal)
            self.assertEqual(result, expected_response)

    def test_start_new_failure_raises_exception(self):
        epic_id = f"epic-{uuid.uuid4().hex}"
        proposal = f"proposal-{uuid.uuid4().hex}"
        status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        error_text = f"error-{uuid.uuid4().hex}"

        with patch("skills.none.requests.post") as mock_post:
            mock_post.return_value.status_code = status_code
            mock_post.return_value.text = error_text

            with self.assertRaises(Exception) as ctx:
                start_new(epic_id, proposal)
            
            self.assertIn(str(status_code), str(ctx.exception))
            self.assertIn(error_text, str(ctx.exception))

    def test_epic_completion_proposal_handler(self):
        completed_epic_id = f"epic-{uuid.uuid4().hex}"
        risk_context = {f"risk_{uuid.uuid4().hex}": random.randint(1, 100)}
        generation_seed = random.randint(1000, 9999)

        mock_file = mock_open()
        with patch("skills.none.open", mock_file):
            result = epic_completion_proposal_handler(completed_epic_id, risk_context, generation_seed)

        self.assertIn("new_direction_id", result)
        self.assertTrue(result["new_direction_id"].startswith("dir-"))
        self.assertEqual(result["source_epic"], completed_epic_id)
        self.assertEqual(result["proposal_file_path"], f"proposal_{completed_epic_id}.txt")

        mock_file.assert_called_once_with(f"proposal_{completed_epic_id}.txt", "w", encoding="utf-8")
        
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn(completed_epic_id, written_content)
        self.assertIn(str(generation_seed), written_content)
        self.assertIn(json.dumps(risk_context), written_content)

if __name__ == "__main__":
    unittest.main()