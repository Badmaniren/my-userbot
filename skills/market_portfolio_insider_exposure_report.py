import os
import json

from skills.db_storage import db_storage, DBStorage, save_report_state, get_report_state


class MarketPortfolioInsiderExposureReporter:
    def __init__(self, payload_data=None):
        self.payload_data = payload_data or {}

    def build_report(self):
        db = self.payload_data.get('db_storage')
        exposure = {}
        if db and hasattr(db, 'fetch_exposure_data'):
            exposure = db.fetch_exposure_data()

        report_id = self.payload_data.get('report_id', 'default_id')
        if exposure and isinstance(exposure, dict):
            exposure_metric = list(exposure.values())[0]
        else:
            exposure_metric = self.payload_data.get('exposure_metric', 0)

        report = {
            'report_id': report_id,
            'exposure_metric': exposure_metric,
            'status': 'active'
        }

        os.makedirs('reports', exist_ok=True)
        report_file = os.path.join('reports', f'exposure_report_{report_id}.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f)

        save_report_state(report_id, report)
        return report

    def _internal_token_resolver(self):
        return "mock_token"

    def process_exposure_streams(self):
        extractor = self.payload_data.get('extractor_tool_1790087207')
        if extractor and hasattr(extractor, 'extract_stream'):
            extractor.extract_stream()

        monitor = self.payload_data.get('market_portfolio_monitor')
        if monitor and hasattr(monitor, 'evaluate_risk'):
            monitor.evaluate_risk()

        token = self._internal_token_resolver()
        return [token]

    def compile_anomaly_section(self):
        detector = self.payload_data.get('market_anomaly_detector')
        if detector and hasattr(detector, 'detect_exposure_spikes'):
            return detector.detect_exposure_spikes()
        return {'anomaly_score': 0.0, 'flagged': False}

    def trigger_alerts(self, alert_msg):
        dispatcher = self.payload_data.get('market_portfolio_alert_dispatcher')
        if dispatcher and hasattr(dispatcher, 'dispatch_signal'):
            return dispatcher.dispatch_signal(alert_msg)
        return True

    def run_audit_check(self):
        hub = self.payload_data.get('market_portfolio_audit_compliance_hub')
        exporter = self.payload_data.get('market_portfolio_audit_log_exporter')

        comp_res = hub.verify_compliance() if hub and hasattr(hub, 'verify_compliance') else {'compliant': True, 'hash': 'abc'}
        if exporter and hasattr(exporter, 'export'):
            exporter.export()
        return comp_res


def generate_insider_exposure_report(payload_data):
    reporter = MarketPortfolioInsiderExposureReporter(payload_data)
    return reporter.build_report()
