from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.market_portfolio_alert_dispatcher import (
    dispatch_portfolio_alerts,
    send_telegram_notification
)

def audit_compliance_and_notify(
    storage_file,
    export_path,
    telegram_token,
    chat_id,
    symbol,
    url,
    severity_level,
    min_threshold,
    channels
):
    hub = MarketPortfolioAuditComplianceHub(storage_file=storage_file)
    if hub.check_compliance_integrity():
        dispatch_portfolio_alerts(
            symbol=symbol,
            url=url,
            telegram_token=telegram_token,
            chat_id=chat_id,
            storage_file=storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=channels
        )
        return True
    return False

class MarketPortfolioAuditAlertNotifierService:
    def __init__(self, db_storage, token, chat_id):
        self.db_storage = db_storage
        self.token = token
        self.chat_id = chat_id
        self.hub = MarketPortfolioAuditComplianceHub(storage_file=db_storage)

    def trigger_alert_on_violation(self, message):
        self.hub.verify_log_integrity()
        send_telegram_notification(
            token=self.token,
            chat_id=self.chat_id,
            message=message
        )

    def process_and_audit_stream(self, export_path, stream):
        res = self.hub.process_audit_stream_data(
            export_path=export_path,
            stream=stream
        )
        summary = self.hub.get_audit_stream_summary()
        if summary is not None:
            return summary
        return res