from skills.incident_forensics_synthesizer import IncidentForensicsSynthesizer
from skills.incident_business_loss_reporter import IncidentBusinessLossReporter


class IncidentForensicsReportBridge:
    def __init__(self, financial_evaluator=None, impact_analyzer=None, forensics_synthesizer=None, business_loss_reporter=None):
        if forensics_synthesizer is not None:
            self.forensics_synthesizer = forensics_synthesizer
        else:
            self.forensics_synthesizer = IncidentForensicsSynthesizer()

        if business_loss_reporter is not None:
            self.business_loss_reporter = business_loss_reporter
        else:
            self.business_loss_reporter = IncidentBusinessLossReporter(
                financial_evaluator=financial_evaluator,
                impact_analyzer=impact_analyzer
            )

    def generate_comprehensive_report(
        self,
        incident_id,
        module_name,
        exception,
        traceback_str,
        financial_data,
        export_path,
        format_type="json"
    ):
        forensics_result = self.forensics_synthesizer.synthesize(
            module_name=module_name,
            exception=exception,
            traceback_str=traceback_str,
            incident_id=incident_id
        )

        business_loss_result = self.business_loss_reporter.generate_report(
            incident_id=incident_id,
            financial_data=financial_data,
            forensics_data=forensics_result
        )

        export_status = self.business_loss_reporter.export_report(
            business_loss_result,
            format_type
        )

        if isinstance(export_path, str) and format_type == "json":
            import json
            import os
            os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
            if not isinstance(export_status, str) or not export_status.startswith("Exported successfully"):
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "forensics": forensics_result,
                        "business_loss": business_loss_result
                    }, f)

        return {
            "forensics": forensics_result,
            "business_loss": business_loss_result,
            "export_status": export_status
        }

    def stream_report_package(
        self,
        incident_id,
        financial_data,
        format_type="json"
    ):
        report_data = self.business_loss_reporter.generate_report(
            incident_id=incident_id,
            financial_data=financial_data
        )
        return self.business_loss_reporter.export_report(report_data, format_type)