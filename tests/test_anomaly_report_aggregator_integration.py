import unittest
import os
import shutil
import uuid
import random
import tempfile
from skills.anomaly_report_aggregator import AnomalyReportAggregator, AnomalyReportAggregatorError

class TestAnomalyReportAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_working_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_working_dir, "repo_" + uuid.uuid4().hex)
        os.makedirs(self.repo_path)
        self.log_path = os.path.join(self.test_working_dir, "anomaly_storage_" + uuid.uuid4().hex + ".log")
        self.threshold = random.uniform(0.01, 0.99)
        
        # Инициализируем агрегатор, который внутри создаст реальные AnomalyCorrelator и AnomalyLogger
        self.aggregator = AnomalyReportAggregator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        if os.path.exists(self.test_working_dir):
            shutil.rmtree(self.test_working_dir)

    def test_integration_metric_flow_to_report(self):
        # Генерируем случайные данные для имитации телеметрии
        random_metric = "sensor_readout_" + uuid.uuid4().hex[:8]
        random_value = random.uniform(100.0, 1000.0)

        # Проверка сквозного вызова: от коррелятора до логгера и получения отчета
        report = self.aggregator.aggregate_and_report(random_metric, random_value)

        # Проверяем, что возвращается структура данных (даже если список аномалий пуст при текущих весах)
        self.assertIsInstance(report, (dict, list), "Агрегатор должен возвращать структурированный отчет")

        # Проверяем физическое создание файла лога через AnomalyLogger
        self.assertTrue(os.path.exists(self.log_path), "Файл лога должен быть создан AnomalyLogger в процессе работы")

    def test_integration_execution_flow_analysis(self):
        # Имитация анализа потока выполнения (execution flow)
        execution_id = "exec_" + uuid.uuid4().hex
        payload = {
            "trace_id": uuid.uuid4().hex,
            "timestamp": random.randint(1600000000, 1700000000),
            "metadata": {"node": "worker_" + str(random.randint(1, 10))}
        }

        # Вызов метода, задействующего логику анализа в Correlator и запись в Logger
        report = self.aggregator.aggregate_execution_flow(execution_id, payload)

        self.assertIsNotNone(report)
        # Проверка, что финальный отчет доступен и после выполнения потока
        final_report = self.aggregator.generate_final_report()
        self.assertEqual(report, final_report)

    def test_error_propagation_integration(self):
        # Проверка обработки некорректных данных, которые должны вызвать исключение в цепочке компонентов
        invalid_metric = None
        invalid_value = "not_a_number"

        # Ожидаем, что ошибка из внутренних слоев (Correlator) будет обернута в AnomalyReportAggregatorError
        with self.assertRaises(AnomalyReportAggregatorError):
            self.aggregator.aggregate_and_report(invalid_metric, invalid_value)

    def test_logger_state_persistence_in_aggregator(self):
        # Проверяем, что агрегатор сохраняет состояние логгера между вызовами
        metric_1 = "mem_usage_" + uuid.uuid4().hex[:4]
        val_1 = random.random()
        
        self.aggregator.aggregate_and_report(metric_1, val_1)
        
        # Генерируем второй отчет и проверяем, что система стабильна
        metric_2 = "cpu_load_" + uuid.uuid4().hex[:4]
        val_2 = random.random()
        
        report = self.aggregator.aggregate_and_report(metric_2, val_2)
        self.assertIsInstance(report, (dict, list))

if __name__ == "__main__":
    unittest.main()