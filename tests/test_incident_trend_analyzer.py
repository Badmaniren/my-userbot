import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from skills.incident_trend_analyzer import start_new

class TestIncidentTrendAnalyzerStartNew(unittest.TestCase):

    def test_start_new_success_flow(self):
        rnd_success = True
        rnd_incident_id = uuid.uuid4().hex
        rnd_error = None
        rnd_raw_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        rnd_patch_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        result = start_new(
            success=rnd_success,
            incident_id=rnd_incident_id,
            error=rnd_error,
            raw_result=rnd_raw_result,
            patch_data=rnd_patch_data
        )

        self.assertIsNotNone(result)
        self.assertTrue(getattr(result, 'success', None) or isinstance(result, dict))
        
        if isinstance(result, dict):
            self.assertEqual(result.get("incident_id"), rnd_incident_id)
            self.assertEqual(result.get("success"), rnd_success)
            self.assertEqual(result.get("error"), rnd_error)
            self.assertEqual(result.get("raw_result"), rnd_raw_result)
            self.assertEqual(result.get("patch_data"), rnd_patch_data)
        else:
            self.assertEqual(result.incident_id, rnd_incident_id)
            self.assertEqual(result.success, rnd_success)
            self.assertEqual(result.error, rnd_error)
            self.assertEqual(result.raw_result, rnd_raw_result)
            self.assertEqual(result.patch_data, rnd_patch_data)

    def test_start_new_failure_flow(self):
        rnd_success = False
        rnd_incident_id = uuid.uuid4().hex
        rnd_error = uuid.uuid4().hex
        rnd_raw_result = uuid.uuid4().hex
        rnd_patch_data = None

        with patch('skills.incident_trend_analyzer.uuid4', return_value=uuid.UUID(int=0)):
            result = start_new(
                success=rnd_success,
                incident_id=rnd_incident_id,
                error=rnd_error,
                raw_result=rnd_raw_result,
                patch_data=rnd_patch_data
            )

        self.assertIsNotNone(result)
        if isinstance(result, dict):
            self.assertEqual(result.get("incident_id"), rnd_incident_id)
            self.assertEqual(result.get("success"), rnd_success)
            self.assertEqual(result.get("error"), rnd_error)
            self.assertEqual(result.get("raw_result"), rnd_raw_result)
            self.assertEqual(result.get("patch_data"), rnd_patch_data)
        else:
            self.assertEqual(result.incident_id, rnd_incident_id)
            self.assertEqual(result.success, rnd_success)
            self.assertEqual(result.error, rnd_error)
            self.assertEqual(result.raw_result, rnd_raw_result)
            self.assertEqual(result.patch_data, rnd_patch_data)

    def test_start_new_stream_handling(self):
        rnd_incident_id = uuid.uuid4().hex
        rnd_stream_data = json.dumps({
            "incident_id": rnd_incident_id,
            "success": True,
            "error": None
        }).encode('utf-8')
        
        stream_mock = io.BytesIO(rnd_stream_data)

        with patch('skills.incident_trend_analyzer.json.load', return_value={"incident_id": rnd_incident_id, "success": True}):
            result = start_new(
                success=True,
                incident_id=rnd_incident_id,
                error=None,
                raw_result=stream_mock.read(),
                patch_data={}
            )

        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()