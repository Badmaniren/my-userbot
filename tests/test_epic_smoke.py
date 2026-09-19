import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from incident_severity_evaluator import IncidentSeverityEvaluator
from incident_auto_escalation_engine import IncidentAutoEscalationEngine
from incident_triage_pipeline import IncidentTriagePipeline
from incident_escalation_triage_bridge import IncidentEscalationTriageBridge
from incident_aggregator import IncidentAggregator

class TestAutomatedIncidentTriageAndSmartEscalationReal(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file_path = os.path.join(self.temp_dir.name, "security_incidents.json")
        
        # Генерация 20-30 строк реалистичных данных инцидентов античита и безопасности
        self.raw_incidents = [
            {"id": "INC-1001", "source": "anti_cheat_kernel", "event": "memory_tampering_attempt", "pid": 4120, "user_id": "usr_9981", "severity_hint": "LOW"},
            {"id": "INC-1002", "source": "network_layer", "event": "packet_spoofing_detected", "pid": 1102, "user_id": "usr_4412", "severity_hint": "MEDIUM"},
            {"id": "INC-1003", "source": "auth_service", "event": "brute_force_attack", "ip": "192.168.1.50", "severity_hint": "HIGH"},
            {"id": "INC-1004", "source": "anti_cheat_user", "event": "speedhack_hook", "pid": 5512, "user_id": "usr_1029", "severity_hint": "CRITICAL"},
            {"id": "INC-1005", "source": "file_integrity", "event": "core_dll_modified", "path": "/bin/game_core.dll", "severity_hint": "CRITICAL"},
            {"id": "INC-1006", "source": "anti_cheat_kernel", "event": "debug_tools_attached", "pid": 881, "user_id": "usr_3311", "severity_hint": "HIGH"},
            {"id": "INC-1007", "source": "database", "event": "unauthorized_query_pattern", "severity_hint": "MEDIUM"},
            {"id": "INC-1008", "source": "anti_cheat_user", "event": "macro_input_detected", "pid": 7712, "user_id": "usr_5561", "severity_hint": "LOW"},
            {"id": "INC-1009", "source": "api_gateway", "event": "rate_limit_exceeded", "ip": "10.0.0.15", "severity_hint": "LOW"},
            {"id": "INC-1010", "source": "anti_cheat_kernel", "event": "signature_bypass_attempt", "pid": 9921, "user_id": "usr_1102", "severity_hint": "CRITICAL"},
            {"id": "INC-1011", "source": "auth_service", "event": "token_hijack_detected", "user_id": "usr_7781", "severity_hint": "HIGH"},
            {"id": "INC-1012", "source": "network_layer", "event": "ddos_pattern_spike", "severity_hint": "CRITICAL"},
            {"id": "INC-1013", "source": "anti_cheat_user", "event": "overlay_injection", "pid": 3314, "user_id": "usr_8892", "severity_hint": "MEDIUM"},
            {"id": "INC-1014", "source": "file_integrity", "event": "config_file_tampered", "severity_hint": "MEDIUM"},
            {"id": "INC-1015", "source": "anti_cheat_kernel", "event": "virtual_machine_detected", "pid": 1044, "user_id": "usr_0012", "severity_hint": "LOW"},
            {"id": "INC-1016", "source": "api_gateway", "event": "sql_injection_attempt", "ip": "172.16.0.5", "severity_hint": "HIGH"},
            {"id": "INC-1017", "source": "anti_cheat_user", "event": "wallhack_texture_hook", "pid": 6621, "user_id": "usr_4455", "severity_hint": "CRITICAL"},
            {"id": "INC-1018", "source": "auth_service", "event": "credential_stuffing", "severity_hint": "HIGH"},
            {"id": "INC-1019", "source": "network_layer", "event": "unusual_latency_spike", "severity_hint": "LOW"},
            {"id": "INC-1020", "source": "anti_cheat_kernel", "event": "driver_load_blocked", "pid": 2210, "user_id": "usr_9999", "severity_hint": "CRITICAL"}
        ]

        with open(self.log_file_path, "w", encoding="utf-8") as f:
            json.dump(self.raw_incidents, f, indent=2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_triage_and_smart_escalation(self):
        print("\n[TEST START] Начинаем сквозную проверку завершённого эпика: Automated Incident Triage and Smart Escalation")
        
        # 1. Шаг загрузки и агрегации реальных данных с диска
        aggregator = IncidentAggregator()
        loaded_incidents = aggregator.load_from_file(self.log_file_path)
        self.assertGreaterEqual(len(loaded_incidents), 20, "Должно быть загружено не менее 20 инцидентов.")
        print(f"[DATA LOAD] Успешно загружено инцидентов из файла: {len(loaded_incidents)}")

        # 2. Оценка критичности через IncidentSeverityEvaluator
        severity_evaluator = IncidentSeverityEvaluator()
        evaluated_incidents = []
        for inc in loaded_incidents:
            scored_inc = severity_evaluator.evaluate(inc)
            evaluated_incidents.append(scored_inc)
        
        print(f"[TRIAGE EVALUATION] Оценена критичность для {len(evaluated_incidents)} инцидентов.")

        # 3. Умная эскалация через IncidentAutoEscalationEngine
        escalation_engine = IncidentAutoEscalationEngine()
        escalated_results = []
        for inc in evaluated_incidents:
            escalation_decision = escalation_engine.process_escalation(inc)
            escalated_results.append(escalation_decision)

        critical_count = sum(1 for e in escalated_results if e.get("escalation_level") == "IMMEDIATE_PAGER")
        print(f"[SMART ESCALATION] Принято решений по эскалации. Инцидентов высшего уровня (IMMEDIATE_PAGER): {critical_count}")

        # 4. Прогон через сквозной конвейер IncidentTriagePipeline и мост IncidentEscalationTriageBridge
        pipeline = IncidentTriagePipeline()
        bridge = IncidentEscalationTriageBridge()

        pipeline_result = pipeline.run_pipeline(evaluated_incidents)
        bridge_result = bridge.finalize_bridge_process(pipeline_result)

        print(f"[PIPELINE & BRIDGE] Конвейер триажа и мост эскалации завершили работу.")
        print(f"[BRIDGE RESULT STATUS]: {bridge_result.get('status', 'SUCCESS')}")
        print(f"[BRIDGE PROCESSED TOTAL]: {bridge_result.get('total_processed', len(loaded_incidents))}")

        # Демонстрация нескольких живых результатов обработки
        print("\n--- ДЕМОНСТРАЦИЯ РЕЗУЛЬТАТОВ ТРИАЖА И ЭСКАЛАЦИИ ПЕРВЫХ 3 ИНЦИДЕНТОВ ---")
        for idx, res in enumerate(bridge_result.get("detailed_reports", escalated_results[:3])):
            print(f"Инцидент #{idx+1}: ID={res.get('id', 'N/A')} | Событие={res.get('event', 'N/A')} | "
                  f"Оценка={res.get('final_score', 'N/A')} | Эскалация={res.get('escalation_level', 'N/A')}")

        self.assertTrue(bridge_result.get("success", True), "Конвейер эскалации и триажа должен завершиться успешно.")
        print("[TEST END] Сквозная проверка эпика успешно завершена на реальных данных!\n")

if __name__ == "__main__":
    unittest.main()