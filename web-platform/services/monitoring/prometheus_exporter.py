"""
Prometheus metrics exporter for Fivoria AI Platform
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# API metrics
api_requests_total = Counter(
    'fivoria_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'fivoria_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# Agent metrics
agent_tasks_total = Counter(
    'fivoria_agent_tasks_total',
    'Total number of agent tasks',
    ['task_type', 'status']
)

agent_task_duration = Histogram(
    'fivoria_agent_task_duration_seconds',
    'Agent task duration in seconds',
    ['task_type']
)

# Model metrics
model_requests_total = Counter(
    'fivoria_model_requests_total',
    'Total number of model inference requests',
    ['model']
)

model_tokens_total = Counter(
    'fivoria_model_tokens_total',
    'Total number of tokens processed',
    ['model']
)

model_request_duration = Histogram(
    'fivoria_model_request_duration_seconds',
    'Model inference duration in seconds',
    ['model']
)

# System metrics
active_users = Gauge(
    'fivoria_active_users',
    'Number of active users'
)

active_projects = Gauge(
    'fivoria_active_projects',
    'Number of active projects'
)

active_conversations = Gauge(
    'fivoria_active_conversations',
    'Number of active conversations'
)

# Service info
service_info = Info(
    'fivoria_service',
    'Fivoria AI Platform service information'
)

service_info.info({
    'version': '1.0.0',
    'environment': 'production'
})

def track_api_request(method: str, endpoint: str, status: int, duration: float):
    """Track API request metrics"""
    api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

def track_agent_task(task_type: str, status: str, duration: float):
    """Track agent task metrics"""
    agent_tasks_total.labels(task_type=task_type, status=status).inc()
    agent_task_duration.labels(task_type=task_type).observe(duration)

def track_model_request(model: str, tokens: int, duration: float):
    """Track model inference metrics"""
    model_requests_total.labels(model=model).inc()
    model_tokens_total.labels(model=model).inc(tokens)
    model_request_duration.labels(model=model).observe(duration)

async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
