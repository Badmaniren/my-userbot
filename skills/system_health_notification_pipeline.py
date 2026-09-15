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
        # Интеграционный метод для обработки списка инцидентов
        aggregation_result = self.aggregator.aggregate_and_report()
        
        # Формируем payload на основе первого критического инцидента, если он есть
        payload = {}
        if incidents_list:
            incident = incidents_list[0]
            payload = {
                "level": incident.get("level"),
                "incident_id": incident.get("id"),
                "message": incident.get("message")
            }
        
        dispatch_result = self.dispatcher.dispatch(target_channel, payload)
        
        return {
            "aggregation_result": aggregation_result,
            "dispatch_result": dispatch_result
        }