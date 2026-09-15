import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
from skills.incident_digest_generator import IncidentDigestGenerator, start_new


class TestIncidentDigestGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = IncidentDigestGenerator()
        self.digest_name = f"digest_{uuid.uuid4().hex}"
        self.output_path = f"{uuid.uuid4().hex}.json"

    def test_generate_digest_valid(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        res = self.generator.generate_digest(payload)
        self.assertEqual(res, json.dumps(payload))

    def test_generate_digest_empty(self):
        res = self.generator.generate_digest({})
        self.assertIsNone(res)

    def test_export_digest_file(self):
        payload = {uuid.uuid4().hex: random.randint(1, 100)}
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = self.generator.export_digest_file(payload, self.output_path)
            self.assertTrue(result)
            mock_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

    def test_export_digest_file_exception(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch("builtins.open", side_effect=Exception(uuid.uuid4().hex)):
            result = self.generator.export_digest_file(payload, self.output_path)
            self.assertFalse(result)

    def test_start_new_empty_stream(self):
        stream = io.BytesIO(b"")
        rand_digest = uuid.uuid4().hex
        rand_path = uuid.uuid4().hex

        with patch('skills.incident_digest_generator.IncidentAggregator') as mock_agg_class, \
             patch('skills.incident_digest_generator.NotificationTemplateEngine') as mock_engine_class:
            
            mock_agg = mock_agg_class.return_value
            mock_agg.process_and_aggregate.return_value = []

            mock_engine = mock_engine_class.return_value

            res = start_new(rand_digest, stream, rand_path)
            self.assertFalse(res)
            mock_engine.render_html.assert_called_once_with(rand_digest)

    def test_start_new_valid_content(self):
        item_key = uuid.uuid4().hex
        item_val = uuid.uuid4().hex
        raw_content = json.dumps([{item_key: item_val}]).encode('utf-8')
        stream = io.BytesIO(raw_content)
        rand_digest = uuid.uuid4().hex
        rand_path = uuid.uuid4().hex
        rendered_text = uuid.uuid4().hex

        with patch('skills.incident_digest_generator.IncidentAggregator') as mock_agg_class, \
             patch('skills.incident_digest_generator.NotificationTemplateEngine') as mock_engine_class, \
             patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            
            mock_agg = mock_agg_class.return_value
            processed_data = [{uuid.uuid4().hex: uuid.uuid4().hex}]
            mock_agg.process_and_aggregate.return_value = processed_data

            mock_engine = mock_engine_class.return_value
            mock_engine.render_text.return_value = rendered_text

            res = start_new(rand_digest, stream, rand_path)
            self.assertTrue(res)
            mock_agg.process_and_aggregate.assert_called_once_with([{item_key: item_val}])
            mock_engine.render_text.assert_called_once_with(rand_digest, processed_data)
            mock_file.assert_called_once_with(rand_path, 'w', encoding='utf-8')
            mock_file().write.assert_called_once_with(str(rendered_text))

    def test_start_new_no_processed_incidents(self):
        raw_content = json.dumps([{uuid.uuid4().hex: uuid.uuid4().hex}]).encode('utf-8')
        stream = io.BytesIO(raw_content)
        rand_digest = uuid.uuid4().hex
        rand_path = uuid.uuid4().hex

        with patch('skills.incident_digest_generator.IncidentAggregator') as mock_agg_class:
            mock_agg = mock_agg_class.return_value
            mock_agg.process_and_aggregate.return_value = []

            res = start_new(rand_digest, stream, rand_path)
            self.assertFalse(res)

    def test_start_new_exception_handling(self):
        stream = MagicMock()
        stream.read.side_effect = Exception(uuid.uuid4().hex)
        rand_digest = uuid.uuid4().hex
        rand_path = uuid.uuid4().hex

        with self.assertRaises(Exception):
            start_new(rand_digest, stream, rand_path)


if __name__ == '__main__':
    unittest.main()