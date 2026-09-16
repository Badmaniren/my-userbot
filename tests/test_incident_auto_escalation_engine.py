import unittest
from unittest.mock import patch, mock_open
import os
import json
import uuid
import random
import io
from skills import incident_auto_escalation_engine

class TestIncidentAutoEscalationEngine(unittest.TestCase):

    def test_auto_patch_pipeline_integration_with_random_payload(self):
        patch_id_val = uuid.uuid4().hex
        metric_val = random.randint(100, 999)

        with patch('skills.incident_auto_escalation_engine.auto_patch_pipeline') as mock_pipeline:
            mock_pipeline.execute.return_value = {patch_id_val: metric_val}
            engine_instance = incident_auto_escalation_engine.IncidentAutoEscalator()
            random_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
            result = engine_instance.trigger_patch_pipeline(random_payload)

            mock_pipeline.execute.assert_called_once_with(random_payload)
            self.assertEqual(result, {patch_id_val: metric_val})

    def test_dependency_audit_reporter_failure_handling(self):
        pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        err_msg = f"audit_failed_{uuid.uuid4().hex[:6]}"

        with patch('skills.incident_auto_escalation_engine.dependency_audit_reporter') as mock_reporter:
            mock_reporter.audit.side_effect = Exception(err_msg)
            engine_instance = incident_auto_escalation_engine.IncidentAutoEscalator()

            with self.assertRaises(Exception) as ctx:
                engine_instance.audit_dependencies(pkg_name)

            self.assertIn(err_msg, str(ctx.exception))
            mock_reporter.audit.assert_called_once_with(pkg_name)

    def test_error_recovery_hub_dispatch(self):
        inc_id = uuid.uuid4().hex
        err_code = random.randint(500, 599)
        expected_resp = f"recovered_{uuid.uuid4().hex}"

        with patch('skills.incident_auto_escalation_engine.error_recovery_hub') as mock_hub:
            mock_hub.handle.return_value = expected_resp
            engine_instance = incident_auto_escalation_engine.IncidentAutoEscalator()

            res = engine_instance.recover_system(inc_id, err_code)
            self.assertEqual(res, expected_resp)
            mock_hub.handle.assert_called_once_with(inc_id, err_code)

    def test_escalation_triggers_on_high_severity_and_trend(self):
        inc_id = uuid.uuid4().hex
        sev_val = f"SEV-{random.randint(1, 5)}"
        trend_val = f"trend-{uuid.uuid4().hex[:4]}"

        with patch('skills.incident_auto_escalation_engine.incident_severity_evaluator') as mock_sev, \
             patch('skills.incident_auto_escalation_engine.incident_trend_analyzer') as mock_trend:

            mock_sev.evaluate.return_value = sev_val
            mock_trend.analyze.return_value = trend_val

            engine_instance = incident_auto_escalation_engine.IncidentAutoEscalator()
            res = engine_instance.evaluate_and_escalate(inc_id)

            self.assertIn(inc_id, res)
            self.assertIn(sev_val, res)
            self.assertIn(trend_val, res)
            mock_sev.evaluate.assert_called_once_with(inc_id)
            mock_trend.analyze.assert_called_once_with(inc_id)

    def test_incident_auto_escalation_engine_function_with_export(self):
        incident_id = uuid.uuid4().hex
        export_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {
            "incident_id": incident_id,
            "export_path": export_path,
            "random_field": uuid.uuid4().hex
        }

        mock_file = mock_open()
        with patch('os.path.join', return_value=f"{export_path}/escalation_{incident_id}.json") as mock_join, \
             patch('builtins.open', mock_file):

            res = incident_auto_escalation_engine.incident_auto_escalation_engine(payload)

            self.assertTrue(res["is_escalated"])
            self.assertEqual(res["escalated_incident_id"], incident_id)
            self.assertEqual(res["details"], payload)
            mock_join.assert_called_once_with(export_path, f"escalation_{incident_id}.json")
            mock_file.assert_called_once()

    def test_incident_auto_escalation_engine_function_without_export(self):
        incident_id = uuid.uuid4().hex
        payload = {
            "incident_id": incident_id,
            "note": uuid.uuid4().hex
        }

        res = incident_auto_escalation_engine.incident_auto_escalation_engine(payload)

        self.assertTrue(res["is_escalated"])
        self.assertEqual(res["escalated_incident_id"], incident_id)
        self.assertEqual(res["details"], payload)

    def test_fetch_active_incidents_and_notifications(self):
        inc_id = uuid.uuid4().hex
        channel = uuid.uuid4().hex
        formatted_msg = f"msg_{uuid.uuid4().hex}"
        broadcast_res = random.choice([True, False])

        with patch('skills.incident_auto_escalation_engine.incident_aggregator') as mock_agg, \
             patch('skills.incident_auto_escalation_engine.incident_notification_bridge') as mock_bridge, \
             patch('skills.incident_auto_escalation_engine.incident_notification_broadcaster') as mock_broadcaster:

            mock_agg.get_active.return_value = [inc_id]
            mock_bridge.format_message.return_value = formatted_msg
            mock_broadcaster.broadcast.return_value = broadcast_res

            engine = incident_auto_escalation_engine.IncidentAutoEscalator()
            active = engine.fetch_active_incidents()
            self.assertEqual(active, [inc_id])

            notif_res = engine.notify_oncall(inc_id, channel)
            self.assertEqual(notif_res, broadcast_res)
            mock_bridge.format_message.assert_called_once_with(inc_id)
            mock_broadcaster.broadcast.assert_called_once_with(formatted_msg, channel)

    def test_forecasting_and_dispatch(self):
        inc_id = uuid.uuid4().hex
        horizon = random.randint(1, 48)
        forecast_data = {uuid.uuid4().hex: random.random()}
        msg_id = uuid.uuid4().hex
        webhook_url = f"https://{uuid.uuid4().hex}.com/hook"
        dispatch_status = f"status_{uuid.uuid4().hex}"

        with patch('skills.incident_auto_escalation_engine.incident_trend_forecaster') as mock_forecaster, \
             patch('skills.incident_auto_escalation_engine.notification_channel_dispatcher') as mock_dispatcher:

            mock_forecaster.predict.return_value = forecast_data
            mock_dispatcher.dispatch.return_value = dispatch_status

            engine = incident_auto_escalation_engine.IncidentAutoEscalator()

            f_res = engine.forecast_trend(inc_id, horizon)
            self.assertEqual(f_res, forecast_data)
            mock_forecaster.predict.assert_called_once_with(inc_id, horizon)

            d_res = engine.dispatch_alert(msg_id, webhook_url)
            self.assertEqual(d_res, dispatch_status)
            mock_dispatcher.dispatch.assert_called_once_with(msg_id, webhook_url)

    def test_templating_and_webhooks(self):
        tpl_name = uuid.uuid4().hex
        context = {uuid.uuid4().hex: uuid.uuid4().hex}
        rendered_str = f"rendered_{uuid.uuid4().hex}"
        webhook_url = f"https://{uuid.uuid4().hex}.net/api"
        payload = {uuid.uuid4().hex: random.randint(1, 100)}
        webhook_resp = {"status": uuid.uuid4().hex}

        with patch('skills.incident_auto_escalation_engine.notification_template_engine') as mock_engine, \
             patch('skills.incident_auto_escalation_engine.notification_webhook_broadcaster') as mock_broadcaster:

            mock_engine.render.return_value = rendered_str
            mock_broadcaster.send.return_value = webhook_resp

            engine = incident_auto_escalation_engine.IncidentAutoEscalator()

            r_res = engine.render_alert_template(tpl_name, context)
            self.assertEqual(r_res, rendered_str)
            mock_engine.render.assert_called_once_with(tpl_name, context)

            w_res = engine.send_webhook(webhook_url, payload)
            self.assertEqual(w_res, webhook_resp)
            mock_broadcaster.send.assert_called_once_with(webhook_url, payload)

    def test_patch_lifecycle_methods(self):
        patch_id = uuid.uuid4().hex
        delay = random.randint(10, 300)
        metrics = {uuid.uuid4().hex: random.random()}
        validation_res = random.choice([True, False])
        exec_res = uuid.uuid4().hex

        with patch('skills.incident_auto_escalation_engine.patch_auto_executor') as mock_exec, \
             patch('skills.incident_auto_escalation_engine.patch_metric_collector') as mock_metric, \
             patch('skills.incident_auto_escalation_engine.patch_scheduler') as mock_scheduler, \
             patch('skills.incident_auto_escalation_engine.patch_validator') as mock_validator:

            mock_exec.apply.return_value = exec_res
            mock_metric.collect.return_value = metrics
            mock_scheduler.schedule.return_value = True
            mock_validator.validate.return_value = validation_res

            engine = incident_auto_escalation_engine.IncidentAutoEscalator()

            self.assertEqual(engine.execute_patch(patch_id), exec_res)
            self.assertEqual(engine.get_patch_metrics(patch_id), metrics)
            self.assertTrue(engine.schedule_patch(patch_id, delay))
            self.assertEqual(engine.validate_patch(patch_id), validation_res)

            mock_exec.apply.assert_called_once_with(patch_id)
            mock_metric.collect.assert_called_once_with(patch_id)
            mock_scheduler.schedule.assert_called_once_with(patch_id, delay)
            mock_validator.validate.assert_called_once_with(patch_id)

    def test_preventive_patch_and_pypi(self):
        vuln_id = uuid.uuid4().hex
        pkg_name = f"lib-{uuid.uuid4().hex[:6]}"
        latest_ver = f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}"
        apply_res = uuid.uuid4().hex

        with patch('skills.incident_auto_escalation_engine.preventive_patch_applier') as mock_applier, \
             patch('skills.incident_auto_escalation_engine.pypi_client') as mock_pypi, \
             patch('skills.incident_auto_escalation_engine.package_requirement_reader') as mock_reader:

            mock_applier.apply_preventive.return_value = apply_res
            mock_pypi.get_latest_version.return_value = latest_ver
            mock_reader.parse.return_value = [pkg_name]

            engine = incident_auto_escalation_engine.IncidentAutoEscalator()

            self.assertEqual(engine.apply_preventive_patch(vuln_id), apply_res)
            self.assertEqual(engine.check_pypi_version(pkg_name), latest_ver)
            self.assertEqual(engine.read_requirements(io.BytesIO(b'dummy')), [pkg_name])

            mock_applier.apply_preventive.assert_called_once_with(vuln_id)
            mock_pypi.get_latest_version.assert_called_once_with(pkg_name)

    def test_recovery_reports_and_dashboards(self):
        dash_id = uuid.uuid4().hex
        report_id = uuid.uuid4().hex
        fmt = random.choice(["json", "pdf", "csv"])
        dash_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        report_res = uuid.uuid4().hex

        with patch('skills.incident_auto_escalation_engine.recovery_dashboard_generator') as mock_dash, \
             patch('skills.incident_auto_escalation_engine.recovery_report_exporter') as mock_exp:

            mock_dash.generate.return_value = dash_res
            mock_exp.export.return_value = report_res

            engine = incident_auto_escalation_engine.IncidentAutoEscalator()

            self.assertEqual(engine.generate_dashboard(dash_id), dash_res)
            self.assertEqual(engine.export_report(report_id, fmt), report_res)

            mock_dash.generate.assert_called_once_with(dash_id)
            mock_exp.export.assert_called_once_with(report_id, fmt)

    def test_system_health_and_telemetry(self):
        sys_id = uuid.uuid4().hex
        node_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        score = random.randint(0, 100)
        audit_res = uuid.uuid4().hex
        ping_res = random.choice([True, False])
        report_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_val = random.random()

        with patch('skills.incident_auto_escalation_engine.system_health_aggregator') as mock_agg, \
             patch('skills.incident_auto_escalation_engine.system_health_audit_pipeline') as mock_audit, \
             patch('skills.incident_auto_escalation_engine.system_health_monitoring_gateway') as mock_gw, \
             patch('skills.incident_auto_escalation_engine.system_health_reporter') as mock_rep, \
             patch('skills.incident_auto_escalation_engine.system_health_telemetry_collector') as mock_tel, \
             patch('skills.incident_auto_escalation_engine.vulnerability_scanner') as mock_vuln:

            mock_agg.get_score.return_value = score
            mock_audit.run.return_value = audit_res
            mock_gw.ping.return_value = ping_res
            mock_rep.build_report.return_value = report_res
            mock_tel.collect.return_value = telemetry_val
            mock_vuln.scan.return_value = [uuid.uuid4().hex]

            engine = incident_auto_escalation_engine.IncidentAutoEscalator()

            self.assertEqual(engine.get_system_health(sys_id), score)
            self.assertEqual(engine.run_health_audit(), audit_res)
            self.assertEqual(engine.ping_gateway(node_id), ping_res)
            self.assertEqual(engine.build_health_report(), report_res)
            self.assertEqual(engine.collect_telemetry(metric_name), telemetry_val)
            self.assertEqual(len(engine.scan_vulnerabilities(node_id)), 1)

            mock_agg.get_score.assert_called_once_with(sys_id)
            mock_audit.run.assert_called_once()
            mock_gw.ping.assert_called_once_with(node_id)
            mock_rep.build_report.assert_called_once()
            mock_tel.collect.assert_called_once_with(metric_name)
            mock_vuln.scan.assert_called_once_with(node_id)

if __name__ == '__main__':
    unittest.main()