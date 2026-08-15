"""
Experiment Tracking Module
Integrates with MLflow for experiment tracking and management
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Experiment statuses"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"
    SCHEDULED = "scheduled"


@dataclass
class ExperimentConfig:
    """Experiment configuration"""
    experiment_id: str
    name: str
    description: str
    model_config: Dict[str, Any]
    training_config: Dict[str, Any]
    data_config: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentRun:
    """Experiment run metadata"""
    run_id: str
    experiment_id: str
    status: ExperimentStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    model_checkpoint: Optional[str] = None
    error: Optional[str] = None


class ExperimentTracker:
    """Base experiment tracker"""

    def __init__(self, tracking_uri: str = "./mlruns"):
        self.tracking_uri = tracking_uri
        self.experiments: Dict[str, ExperimentConfig] = {}
        self.runs: Dict[str, ExperimentRun] = {}
        self._initialize_tracking()

    def _initialize_tracking(self):
        """Initialize tracking backend"""
        Path(self.tracking_uri).mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized experiment tracking at {self.tracking_uri}")

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str,
        model_config: Dict,
        training_config: Dict,
        data_config: Dict,
        tags: List[str] = None
    ) -> ExperimentConfig:
        """Create a new experiment"""
        experiment = ExperimentConfig(
            experiment_id=experiment_id,
            name=name,
            description=description,
            model_config=model_config,
            training_config=training_config,
            data_config=data_config,
            tags=tags or []
        )
        
        self.experiments[experiment_id] = experiment
        self._save_experiment(experiment)
        
        logger.info(f"Created experiment: {experiment_id}")
        return experiment

    def start_run(
        self,
        experiment_id: str,
        run_id: str = None,
        parameters: Dict = None
    ) -> ExperimentRun:
        """Start a new experiment run"""
        if run_id is None:
            run_id = f"{experiment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        run = ExperimentRun(
            run_id=run_id,
            experiment_id=experiment_id,
            status=ExperimentStatus.RUNNING,
            start_time=datetime.now(),
            parameters=parameters or {}
        )
        
        self.runs[run_id] = run
        self._save_run(run)
        
        logger.info(f"Started run: {run_id}")
        return run

    def log_metric(self, run_id: str, key: str, value: float, step: int = None):
        """Log a metric for a run"""
        if run_id not in self.runs:
            logger.warning(f"Run {run_id} not found")
            return
        
        metric_key = f"{key}_step_{step}" if step is not None else key
        self.runs[run_id].metrics[metric_key] = value
        self._save_run(self.runs[run_id])

    def log_metrics(self, run_id: str, metrics: Dict[str, float], step: int = None):
        """Log multiple metrics for a run"""
        for key, value in metrics.items():
            self.log_metric(run_id, key, value, step)

    def log_parameter(self, run_id: str, key: str, value: Any):
        """Log a parameter for a run"""
        if run_id not in self.runs:
            logger.warning(f"Run {run_id} not found")
            return
        
        self.runs[run_id].parameters[key] = value
        self._save_run(self.runs[run_id])

    def log_parameters(self, run_id: str, parameters: Dict[str, Any]):
        """Log multiple parameters for a run"""
        for key, value in parameters.items():
            self.log_parameter(run_id, key, value)

    def log_artifact(self, run_id: str, artifact_path: str):
        """Log an artifact for a run"""
        if run_id not in self.runs:
            logger.warning(f"Run {run_id} not found")
            return
        
        self.runs[run_id].artifacts.append(artifact_path)
        self._save_run(self.runs[run_id])

    def log_model(self, run_id: str, model_path: str):
        """Log a model checkpoint for a run"""
        if run_id not in self.runs:
            logger.warning(f"Run {run_id} not found")
            return
        
        self.runs[run_id].model_checkpoint = model_path
        self._save_run(self.runs[run_id])

    def end_run(self, run_id: str, status: ExperimentStatus = ExperimentStatus.COMPLETED, error: str = None):
        """End an experiment run"""
        if run_id not in self.runs:
            logger.warning(f"Run {run_id} not found")
            return
        
        self.runs[run_id].status = status
        self.runs[run_id].end_time = datetime.now()
        if error:
            self.runs[run_id].error = error
        
        self._save_run(self.runs[run_id])
        logger.info(f"Ended run {run_id} with status {status.value}")

    def get_run(self, run_id: str) -> Optional[ExperimentRun]:
        """Get a run by ID"""
        return self.runs.get(run_id)

    def get_experiment_runs(self, experiment_id: str) -> List[ExperimentRun]:
        """Get all runs for an experiment"""
        return [run for run in self.runs.values() if run.experiment_id == experiment_id]

    def get_best_run(self, experiment_id: str, metric: str, minimize: bool = False) -> Optional[ExperimentRun]:
        """Get the best run for an experiment based on a metric"""
        runs = self.get_experiment_runs(experiment_id)
        
        if not runs:
            return None
        
        best_run = None
        best_value = float('inf') if minimize else float('-inf')
        
        for run in runs:
            for key, value in run.metrics.items():
                if key.startswith(metric):
                    if minimize:
                        if value < best_value:
                            best_value = value
                            best_run = run
                    else:
                        if value > best_value:
                            best_value = value
                            best_run = run
        
        return best_run

    def compare_runs(self, run_ids: List[str]) -> Dict[str, Dict]:
        """Compare multiple runs"""
        comparison = {}
        
        for run_id in run_ids:
            run = self.get_run(run_id)
            if run:
                comparison[run_id] = {
                    'status': run.status.value,
                    'start_time': run.start_time.isoformat(),
                    'end_time': run.end_time.isoformat() if run.end_time else None,
                    'metrics': run.metrics,
                    'parameters': run.parameters
                }
        
        return comparison

    def _save_experiment(self, experiment: ExperimentConfig):
        """Save experiment to disk"""
        exp_path = Path(self.tracking_uri) / "experiments" / experiment.experiment_id
        exp_path.mkdir(parents=True, exist_ok=True)
        
        with open(exp_path / "config.json", 'w') as f:
            json.dump(experiment.__dict__, f, indent=2, default=str)

    def _save_run(self, run: ExperimentRun):
        """Save run to disk"""
        exp_path = Path(self.tracking_uri) / "experiments" / run.experiment_id
        run_path = exp_path / "runs" / run.run_id
        run_path.mkdir(parents=True, exist_ok=True)
        
        with open(run_path / "run.json", 'w') as f:
            json.dump(run.__dict__, f, indent=2, default=str)


class MLflowTracker(ExperimentTracker):
    """MLflow integration for experiment tracking"""

    def __init__(self, tracking_uri: str = "./mlruns"):
        super().__init__(tracking_uri)
        self.mlflow_available = self._check_mlflow()
        
        if self.mlflow_available:
            self._initialize_mlflow()

    def _check_mlflow(self) -> bool:
        """Check if MLflow is available"""
        try:
            import mlflow
            return True
        except ImportError:
            logger.warning("MLflow not available. Using local tracking.")
            return False

    def _initialize_mlflow(self):
        """Initialize MLflow"""
        try:
            import mlflow
            mlflow.set_tracking_uri(self.tracking_uri)
            logger.info(f"MLflow tracking initialized at {self.tracking_uri}")
        except Exception as e:
            logger.error(f"Failed to initialize MLflow: {e}")
            self.mlflow_available = False

    def create_experiment(self, experiment_id: str, name: str, description: str, **kwargs) -> ExperimentConfig:
        """Create experiment with MLflow"""
        # Create local experiment
        experiment = super().create_experiment(experiment_id, name, description, **kwargs)
        
        # Create MLflow experiment
        if self.mlflow_available:
            try:
                import mlflow
                mlflow.create_experiment(name)
            except Exception as e:
                logger.error(f"Failed to create MLflow experiment: {e}")
        
        return experiment

    def start_run(self, experiment_id: str, run_id: str = None, parameters: Dict = None) -> ExperimentRun:
        """Start run with MLflow"""
        # Start local run
        run = super().start_run(experiment_id, run_id, parameters)
        
        # Start MLflow run
        if self.mlflow_available:
            try:
                import mlflow
                experiment = self.experiments.get(experiment_id)
                mlflow.start_run(run_name=run.run_id, experiment_id=experiment.name if experiment else None)
                
                # Log parameters
                if parameters:
                    mlflow.log_params(parameters)
            except Exception as e:
                logger.error(f"Failed to start MLflow run: {e}")
        
        return run

    def log_metric(self, run_id: str, key: str, value: float, step: int = None):
        """Log metric with MLflow"""
        super().log_metric(run_id, key, value, step)
        
        if self.mlflow_available:
            try:
                import mlflow
                mlflow.log_metric(key, value, step=step)
            except Exception as e:
                logger.error(f"Failed to log MLflow metric: {e}")

    def log_parameter(self, run_id: str, key: str, value: Any):
        """Log parameter with MLflow"""
        super().log_parameter(run_id, key, value)
        
        if self.mlflow_available:
            try:
                import mlflow
                mlflow.log_param(key, str(value))
            except Exception as e:
                logger.error(f"Failed to log MLflow parameter: {e}")

    def log_artifact(self, run_id: str, artifact_path: str):
        """Log artifact with MLflow"""
        super().log_artifact(run_id, artifact_path)
        
        if self.mlflow_available:
            try:
                import mlflow
                mlflow.log_artifact(artifact_path)
            except Exception as e:
                logger.error(f"Failed to log MLflow artifact: {e}")

    def log_model(self, run_id: str, model_path: str):
        """Log model with MLflow"""
        super().log_model(run_id, model_path)
        
        if self.mlflow_available:
            try:
                import mlflow.pytorch
                mlflow.pytorch.log_model(model_path, "model")
            except Exception as e:
                logger.error(f"Failed to log MLflow model: {e}")

    def end_run(self, run_id: str, status: ExperimentStatus = ExperimentStatus.COMPLETED, error: str = None):
        """End run with MLflow"""
        super().end_run(run_id, status, error)
        
        if self.mlflow_available:
            try:
                import mlflow
                mlflow.end_run()
            except Exception as e:
                logger.error(f"Failed to end MLflow run: {e}")


class TrainingMonitor:
    """Monitor training progress and log to experiment tracker"""

    def __init__(self, tracker: ExperimentTracker, run_id: str):
        self.tracker = tracker
        self.run_id = run_id
        self.step = 0

    def log_training_step(
        self,
        loss: float,
        learning_rate: float,
        throughput: float = None,
        gpu_memory: float = None,
        **kwargs
    ):
        """Log training step metrics"""
        metrics = {
            'loss': loss,
            'learning_rate': learning_rate
        }
        
        if throughput is not None:
            metrics['throughput'] = throughput
        
        if gpu_memory is not None:
            metrics['gpu_memory'] = gpu_memory
        
        metrics.update(kwargs)
        
        self.tracker.log_metrics(self.run_id, metrics, step=self.step)
        self.step += 1

    def log_evaluation(self, eval_metrics: Dict[str, float]):
        """Log evaluation metrics"""
        self.tracker.log_metrics(self.run_id, eval_metrics, step=self.step)

    def log_hyperparameters(self, hyperparameters: Dict[str, Any]):
        """Log hyperparameters"""
        self.tracker.log_parameters(self.run_id, hyperparameters)


def main():
    """Example usage"""
    tracker = MLflowTracker("./mlruns")
    
    # Create experiment
    experiment = tracker.create_experiment(
        experiment_id="fivoria-100b-pretrain",
        name="Fivoria 100B Pretraining",
        description="Initial pretraining run for 100B model",
        model_config={'layers': 80, 'hidden_dim': 12288},
        training_config={'batch_size': 32, 'learning_rate': 1e-4},
        data_config={'dataset': 'fivoria-corpus-v1'},
        tags=['pretraining', '100b']
    )
    
    # Start run
    run = tracker.start_run(experiment.experiment_id, parameters={'warmup_steps': 1000})
    
    # Log some metrics
    tracker.log_metric(run.run_id, 'loss', 5.2, step=0)
    tracker.log_metric(run.run_id, 'loss', 4.8, step=100)
    tracker.log_metric(run.run_id, 'loss', 4.5, step=200)
    
    # End run
    tracker.end_run(run.run_id)
    
    print(f"Experiment completed: {experiment.experiment_id}")


if __name__ == "__main__":
    main()
