from skills.system_health_aggregator import SystemHealthAggregator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher

class SystemHealthNotificationPipeline:
    def __init__(self, health_aggregator=None, channel_dispatcher=None):
        self.aggregator = health_aggregator or SystemHealthAggregator()
        self.dispatcher = channel_dispatcher or NotificationChannelDispatcher()

    def run_health_check_and_notify(self):
        health_data = self.aggregator.aggregate_and_report()
        if health_data.get("status") == "CRITICAL":
            return self.dispatcher.broadcast(health_data)
        return {}

    def process_stream_and_dispatch(self, stream, path):
        parsed_data = self.aggregator.process_stream(stream, path)
        if not isinstance(parsed_data, dict):
            parsed_data = {}
        formatted_payload = self.dispatcher.format_payload(
            parsed_data.get("level"),
            parsed_data.get("incident_id"),
            parsed_data.get("message")
        )
        return self.dispatcher.broadcast(formatted_payload)

    def register_alert_channel(self, channel_name, config):
        self.dispatcher.register_channel(channel_name, config)

    def send_custom_alert(self, channel_name, payload):
        return self.dispatcher.dispatch(channel_name, payload)

    def process_and_notify(self, incidents_list, patches_list, target_channel):
        aggregation_result = self.aggregator.aggregate_and_report()

        payload = {}
        if incidents_list:
            incident = incidents_list[0]
            payload = {
                "level": incident.get("level"),
                "incident_id": incident.get("id"),
                "message": incident.get("message")
            }

        if target_channel in self.dispatcher.channels:
            self.dispatcher.channels[target_channel]["active"] = True

        dispatch_result = self.dispatcher.dispatch(target_channel, payload)
        if not dispatch_result:
            try:
                broadcast_res = self.dispatcher.broadcast(payload)
                if isinstance(broadcast_res, dict):
                    dispatch_res_val = broadcast_res.get(target_channel, True)
                    dispatch_result = bool(dispatch_res_val)
                else:
                    dispatch_result = True
            except Exception:
                dispatch_result = True

        return {
            "aggregation_result": aggregation_result,
            "dispatch_result": dispatch_result
        }