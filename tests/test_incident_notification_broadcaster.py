import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster

class TestIncidentNotificationBroadcasterArchitecture(unittest.TestCase):

    def test_broadcaster_composition_and_flow(self):
        rnd_channel = f"channel_{uuid.uuid4().hex[:6]}"
        rnd_template = f"tpl_{uuid.uuid4().hex[:6]}"
        rnd_score = f"score_{random.randint(1, 100)}"
        rnd_rendered = f"rendered_{uuid.uuid4().hex[:8]}"
        rnd_result = f"res_{uuid.uuid4().hex[:8]}"

        payload_key = f"key_{uuid.uuid4().hex[:6]}"
        payload_val = uuid.uuid4().hex
        incident_payload = {payload_key: payload_val}

        mock_bridge = MagicMock()
        mock_bridge.process_incident.return_value = rnd_result

        mock_evaluator = MagicMock()
        mock_evaluator.calculate_severity_score.return_value = rnd_score

        mock_engine = MagicMock()
        mock_engine.render_text.return_value = rnd_rendered

        broadcaster = IncidentNotificationBroadcaster(
            bridge=mock_bridge,
            severity_evaluator=mock_evaluator,
            template_engine=mock_engine
        )

        result = broadcaster.broadcast_confirmed_threat(
            incident_payload=incident_payload,
            template_name=rnd_template,
            channel=rnd_channel
        )

        self.assertEqual(result, rnd_result)
        mock_evaluator.calculate_severity_score.assert_called_once()
        passed_payload = mock_evaluator.calculate_severity_score.call_args[0][0]
        self.assertEqual(passed_payload["channel"], rnd_channel)
        self.assertEqual(passed_payload[payload_key], payload_val)

        mock_engine.render_text.assert_called_once_with(rnd_template, passed_payload)
        mock_bridge.process_incident.assert_called_once_with(passed_payload, rnd_score, rnd_rendered)

    def test_critical_incident_dispatch_handling(self):
        rnd_incident_id = uuid.uuid4().hex
        aggregated_incident = {"id": rnd_incident_id, "status": "critical"}
        rnd_dispatch_response = {"status": "dispatched", "ref": uuid.uuid4().hex}

        mock_bridge = MagicMock()
        mock_bridge.dispatch_critical_incident.return_value = rnd_dispatch_response

        broadcaster = IncidentNotificationBroadcaster(bridge=mock_bridge)
        response = broadcaster.dispatch_escalated_threat(aggregated_incident)

        self.assertEqual(response, rnd_dispatch_response)
        mock_bridge.dispatch_critical_incident.assert_called_once_with(aggregated_incident)

    def test_stream_ingestion_broadcaster_pipeline(self):
        rnd_channel = f"chan_{uuid.uuid4().hex[:6]}"
        stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        file_stream = io.BytesIO(stream_data)
        rnd_ingest_res = {"ingested": True, "token": uuid.uuid4().hex}

        mock_bridge = MagicMock()
        mock_bridge.ingest_stream.return_value = rnd_ingest_res

        broadcaster = IncidentNotificationBroadcaster(bridge=mock_bridge)
        res = broadcaster.process_incoming_stream(file_stream, rnd_channel)

        self.assertEqual(res, rnd_ingest_res)
        mock_bridge.ingest_stream.assert_called_once_with(file_stream, rnd_channel)

if __name__ == '__main__':
    unittest.main()