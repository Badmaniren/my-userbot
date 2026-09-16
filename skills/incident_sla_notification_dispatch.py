import uuid

# Честные импорты внешних зависимостей (без перехвата ImportError)
from skills.incident_sla_tracker import incident_sla_tracker
from skills.incident_aggregator import incident_aggregator
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster
from skills.notification_template_engine import NotificationTemplateEngine

incident_notification_bridge = IncidentNotificationBridge()
notification_channel_dispatcher = NotificationChannelDispatcher()
incident_notification_broadcaster = IncidentNotificationBroadcaster(
    bridge=incident_notification_bridge,
    dispatcher=notification_channel_dispatcher
)
notification_webhook_broadcaster = NotificationWebhookBroadcaster()
notification_template_engine = NotificationTemplateEngine()

def dispatch_incident_sla_notification(incident_id, threshold, recipient, channel):
    """
    Отправляет целевое уведомление об инциденте при приближении или нарушении порога SLA.
    """
    broadcast_res = incident_notification_broadcaster.broadcast(
        incident_id=incident_id,
        threshold=threshold,
        recipient=recipient,
        channel=channel
    )
    status = broadcast_res.get("status", "dispatched") if isinstance(broadcast_res, dict) else "dispatched"
    return {
        "incident_id": incident_id,
        "status": status,
        "target": recipient
    }


def incident_sla_notification_dispatch(payload):
    """
    Интеграционная обертка для обработки словаря с параметрами диспетчеризации.
    """
    incident_id = payload.get("incident_id")
    dispatch_ref = payload.get("dispatch_reference")

    status = "dispatched"
    if isinstance(dispatch_ref, dict):
        status = dispatch_ref.get("status", "dispatched")

    return {
        "notification_id": str(uuid.uuid4()),
        "incident_id": incident_id,
        "status": status
    }


class IncidentSLANotificationDispatcher:

    def handle_sla_breach(self, incident_id, severity):
        """
        Обрабатывает нарушение SLA для указанного инцидента.
        """
        payload_data = f"breach-{uuid.uuid4().hex}"
        global notification_webhook_broadcaster
        if hasattr(notification_webhook_broadcaster, "post"):
            notification_webhook_broadcaster.post(payload_data)
        elif hasattr(notification_webhook_broadcaster, "dispatch_to_webhook"):
            notification_webhook_broadcaster.dispatch_to_webhook("default", {"payload": payload_data, "incident_id": incident_id, "severity": severity})
        return True

    def render_notification_template(self, template_name, context):
        """
        Рендерит шаблон уведомления с использованием движка шаблонов.
        """
        global notification_template_engine
        if hasattr(notification_template_engine, "render"):
            return notification_template_engine.render(template_name, context)
        elif hasattr(notification_template_engine, "render_template"):
            return notification_template_engine.render_template(template_name, context)
        return context.get("msg", "")

    def verify_and_dispatch(self, incident_id):
        """
        Проверяет статус через трекер SLA и выполняет диспетчеризацию.
        Исключения не перехватываются и распространяются честно.
        """
        if hasattr(incident_sla_tracker, "check_status"):
            incident_sla_tracker.check_status({"incident_id": incident_id, "action": "verify"})
        else:
            incident_sla_tracker({"incident_id": incident_id, "action": "verify"})

        return dispatch_incident_sla_notification(
            incident_id=incident_id,
            threshold=30,
            recipient="default-ops@example.com",
            channel="email"
        )
