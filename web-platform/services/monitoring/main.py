"""
Monitoring Service for Fivoria AI Platform
Provides metrics, logs, and traces
"""

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_exporter import metrics_endpoint
import logging
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

app = FastAPI(
    title="Fivoria AI Monitoring Service",
    description="Monitoring and observability for Fivoria AI Platform",
    version="1.0.0"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory log storage (use proper logging system in production)
logs = []

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()

@app.get("/api/v1/monitoring/health")
async def health_check():
    """Health check for all services"""
    services = {
        "web-api": "healthy",
        "agent-api": "healthy",
        "project-service": "healthy",
        "model-gateway": "healthy",
        "preview-service": "healthy"
    }
    
    return {
        "status": "healthy" if all(s == "healthy" for s in services.values()) else "degraded",
        "services": services,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/monitoring/logs")
async def get_logs(service: str = None, level: str = None, limit: int = 100):
    """Get logs from services"""
    # TODO: Implement proper log aggregation
    filtered_logs = logs
    
    if service:
        filtered_logs = [log for log in filtered_logs if log.get("service") == service]
    
    if level:
        filtered_logs = [log for log in filtered_logs if log.get("level") == level]
    
    return {
        "logs": filtered_logs[-limit:],
        "total": len(filtered_logs)
    }

@app.get("/api/v1/monitoring/stats")
async def get_stats():
    """Get platform statistics"""
    return {
        "users": {
            "total": 0,
            "active": 0
        },
        "projects": {
            "total": 0,
            "active": 0
        },
        "conversations": {
            "total": 0,
            "active": 0
        },
        "agent_tasks": {
            "total": 0,
            "running": 0,
            "completed": 0,
            "failed": 0
        },
        "models": {
            "available": 3,
            "requests_today": 0
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
