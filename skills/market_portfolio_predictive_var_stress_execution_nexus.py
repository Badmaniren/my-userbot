import os
import logging
from skills.market_portfolio_predictive_var_hedge_synthesizer import PredictiveVarHedgeSynthesizer
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline, ExecutionPipelineError

logger = logging.getLogger(__name__)

class NexusExecutionError(Exception):
    """Custom exception for PredictiveVarStressExecutionNexus failures."""
    pass

class PredictiveVarStressExecutionNexus:
    def __init__(self, db_storage=None, hedge_synthesizer=None, execution_pipeline=None, storage_file=None):
        # Поддерживаем различные параметры инициализации из тестов
        self.storage_file = db_storage or storage_file or "nexus_default.db"
        
        if hedge_synthesizer is not None:
            self.synthesizer = hedge_synthesizer
        else:
            self.synthesizer = PredictiveVarHedgeSynthesizer(db_storage=self.storage_file)
            
        if execution_pipeline is not None:
            self.execution_pipeline = execution_pipeline
        else:
            self.execution_pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)

    def synthesize_var_and_execute(
        self,
        portfolio_id,
        scenario_code,
        simulations,
        horizon_days,
        confidence_level,
        portfolio_value,
        scenario_params,
        iterations,
        request_id,
        symbol,
        percentage,
        shifts
    ):
        try:
            # 1. Синтезируем хеш через синтезатор
            synthesis_result = self.synthesizer.synthesize_and_execute_hedge(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations,
                request_id=request_id,
                symbol=symbol,
                percentage=percentage,
                shifts=shifts
            )
            
            # Извлекаем объем для исполнения, если он есть в результате синтеза, иначе используем дефолтный
            vol = synthesis_result.get("volume", 100) if isinstance(synthesis_result, dict) else 100

            # 2. Исполняем симуляцию через pipeline
            execution_result = self.execution_pipeline.simulate_execution(
                symbol=symbol,
                volume=vol
            )

            return {
                "synthesis": synthesis_result,
                "execution": execution_result
            }
        except ExecutionPipelineError as e:
            raise NexusExecutionError(f"Execution pipeline error: {str(e)}") from e
        except Exception as e:
            if isinstance(e, NexusExecutionError):
                raise e
            raise NexusExecutionError(f"Nexus execution failed: {str(e)}") from e

    def run_stress_var_pipeline_nexus(self, ticker, shifts, volume, scenario_name):
        try:
            return self.execution_pipeline.run_stress_pipeline(ticker, shifts, volume, scenario_name)
        except Exception as e:
            raise NexusExecutionError(f"Stress var pipeline error: {str(e)}") from e

    def process_stream_auto_hedge_and_execute(
        self,
        stream_mock,
        portfolio_id,
        request_id,
        symbol,
        percentage,
        shifts
    ):
        try:
            stream_result = self.synthesizer.process_stream_and_auto_hedge(
                stream_mock=stream_mock,
                portfolio_id=portfolio_id,
                request_id=request_id,
                symbol=symbol,
                percentage=percentage,
                shifts=shifts
            )
            
            # Извлекаем volume для исполнения из контекста или берем стандартный
            volume = 100
            if isinstance(stream_result, dict) and "volume" in stream_result:
                volume = stream_result["volume"]

            execution_status = self.execution_pipeline.run_stress_execution(
                symbol, volume, shifts
            )

            return {
                "stream_result": stream_result,
                "execution_status": execution_status
            }
        except Exception as e:
            raise NexusExecutionError(f"Stream processing and auto hedge error: {str(e)}") from e

    def execute_nexus_stress_hedge_pipeline(
        self,
        portfolio_id,
        portfolio_value,
        scenario_params,
        confidence_level,
        horizon_days,
        iterations,
        request_id,
        symbol,
        percentage,
        shifts,
        scenario_code,
        simulations
    ):
        try:
            # Выполняем комплексную интеграционную цепочку
            synthesis_res = self.synthesizer.synthesize_and_execute_hedge(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations,
                request_id=request_id,
                symbol=symbol,
                percentage=percentage,
                shifts=shifts
            )

            # Гарантируем создание базы данных/файла хранилища при интеграции
            if self.storage_file and not os.path.exists(self.storage_file):
                with open(self.storage_file, "w") as f:
                    f.write("nexus_init")

            return {
                "status": "success",
                "portfolio_id": portfolio_id,
                "request_id": request_id,
                "synthesis": synthesis_res
            }
        except Exception as e:
            raise NexusExecutionError(f"Integration stress hedge pipeline failed: {str(e)}") from e