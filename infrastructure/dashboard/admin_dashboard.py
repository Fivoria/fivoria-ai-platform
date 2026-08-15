"""
Admin Dashboard
Web-based admin interface for monitoring and managing the AI platform
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Fivoria AI Admin Dashboard")


# Data models
class JobStatus(BaseModel):
    job_id: str
    name: str
    status: str
    current_step: int
    total_steps: int
    loss: float
    cluster_id: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]


class ClusterStatus(BaseModel):
    cluster_id: str
    name: str
    status: str
    total_gpus: int
    available_gpus: int
    gpu_type: str
    location: str


class SystemStatus(BaseModel):
    jobs: Dict[str, int]
    clusters: Dict[str, int]
    gpus: Dict[str, int]


# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fivoria AI Admin Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            color: #333;
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            color: #333;
            font-size: 32px;
            font-weight: bold;
        }
        
        .section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .section h2 {
            color: #333;
            font-size: 18px;
            margin-bottom: 15px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        
        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .status-running { background: #d4edda; color: #155724; }
        .status-completed { background: #cce5ff; color: #004085; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-pending { background: #fff3cd; color: #856404; }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }
        
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .refresh-btn:hover {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Fivoria AI Admin Dashboard</h1>
            <p>Monitor and manage your AI training infrastructure</p>
        </div>
        
        <div class="stats-grid" id="stats">
            <div class="stat-card">
                <h3>Total Jobs</h3>
                <div class="value" id="total-jobs">-</div>
            </div>
            <div class="stat-card">
                <h3>Running Jobs</h3>
                <div class="value" id="running-jobs">-</div>
            </div>
            <div class="stat-card">
                <h3>Total GPUs</h3>
                <div class="value" id="total-gpus">-</div>
            </div>
            <div class="stat-card">
                <h3>Available GPUs</h3>
                <div class="value" id="available-gpus">-</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Training Jobs</h2>
            <button class="refresh-btn" onclick="refreshData()">Refresh</button>
            <br><br>
            <table>
                <thead>
                    <tr>
                        <th>Job ID</th>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Progress</th>
                        <th>Loss</th>
                        <th>Cluster</th>
                    </tr>
                </thead>
                <tbody id="jobs-table">
                    <tr><td colspan="6">Loading...</td></tr>
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>GPU Clusters</h2>
            <table>
                <thead>
                    <tr>
                        <th>Cluster ID</th>
                        <th>Name</th>
                        <th>Status</th>
                        <th>GPUs</th>
                        <th>Type</th>
                        <th>Location</th>
                    </tr>
                </thead>
                <tbody id="clusters-table">
                    <tr><td colspan="6">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                
                // Update stats
                document.getElementById('total-jobs').textContent = data.system_status.jobs.total;
                document.getElementById('running-jobs').textContent = data.system_status.jobs.running;
                document.getElementById('total-gpus').textContent = data.system_status.gpus.total;
                document.getElementById('available-gpus').textContent = data.system_status.gpus.available;
                
                // Update jobs table
                const jobsHtml = data.jobs.map(job => `
                    <tr>
                        <td>${job.job_id}</td>
                        <td>${job.name}</td>
                        <td><span class="status-badge status-${job.status}">${job.status}</span></td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${(job.current_step / job.total_steps * 100).toFixed(1)}%"></div>
                            </div>
                            <small>${job.current_step}/${job.total_steps}</small>
                        </td>
                        <td>${job.loss.toFixed(4)}</td>
                        <td>${job.cluster_id}</td>
                    </tr>
                `).join('');
                document.getElementById('jobs-table').innerHTML = jobsHtml || '<tr><td colspan="6">No jobs</td></tr>';
                
                // Update clusters table
                const clustersHtml = data.clusters.map(cluster => `
                    <tr>
                        <td>${cluster.cluster_id}</td>
                        <td>${cluster.name}</td>
                        <td><span class="status-badge status-${cluster.status}">${cluster.status}</span></td>
                        <td>${cluster.available_gpus}/${cluster.total_gpus}</td>
                        <td>${cluster.gpu_type}</td>
                        <td>${cluster.location}</td>
                    </tr>
                `).join('');
                document.getElementById('clusters-table').innerHTML = clustersHtml || '<tr><td colspan="6">No clusters</td></tr>';
                
            } catch (error) {
                console.error('Failed to fetch data:', error);
            }
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshData, 5000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
"""


# Mock control plane (would be injected in production)
class MockControlPlane:
    """Mock control plane for demonstration"""
    
    def get_dashboard_data(self) -> Dict:
        """Get mock dashboard data"""
        return {
            'system_status': {
                'jobs': {
                    'total': 5,
                    'running': 2,
                    'completed': 2,
                    'failed': 1,
                    'queued': 0
                },
                'clusters': {
                    'total': 2,
                    'available': 1,
                    'busy': 1
                },
                'gpus': {
                    'total': 128,
                    'available': 64,
                    'utilized': 64
                }
            },
            'jobs': [
                {
                    'job_id': 'job_001',
                    'name': 'Fivoria-100B Pretraining',
                    'status': 'running',
                    'current_step': 45000,
                    'total_steps': 100000,
                    'loss': 2.3456,
                    'cluster_id': 'cluster-1',
                    'created_at': '2024-01-15T10:00:00',
                    'started_at': '2024-01-15T10:05:00',
                    'completed_at': None,
                    'error': None
                },
                {
                    'job_id': 'job_002',
                    'name': 'Fivoria-7B SFT',
                    'status': 'running',
                    'current_step': 2500,
                    'total_steps': 10000,
                    'loss': 1.2345,
                    'cluster_id': 'cluster-2',
                    'created_at': '2024-01-16T08:00:00',
                    'started_at': '2024-01-16T08:02:00',
                    'completed_at': None,
                    'error': None
                },
                {
                    'job_id': 'job_003',
                    'name': 'Fivoria-1B Test',
                    'status': 'completed',
                    'current_step': 10000,
                    'total_steps': 10000,
                    'loss': 0.9876,
                    'cluster_id': 'cluster-1',
                    'created_at': '2024-01-14T12:00:00',
                    'started_at': '2024-01-14T12:01:00',
                    'completed_at': '2024-01-14T18:30:00',
                    'error': None
                }
            ],
            'clusters': [
                {
                    'cluster_id': 'cluster-1',
                    'name': 'Primary Training Cluster',
                    'status': 'busy',
                    'total_gpus': 64,
                    'available_gpus': 0,
                    'gpu_type': 'A100',
                    'location': 'us-east-1'
                },
                {
                    'cluster_id': 'cluster-2',
                    'name': 'Secondary Training Cluster',
                    'status': 'available',
                    'total_gpus': 64,
                    'available_gpus': 64,
                    'gpu_type': 'A100',
                    'location': 'us-west-2'
                }
            ]
        }


# Initialize mock control plane
control_plane = MockControlPlane()


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve dashboard HTML"""
    return DASHBOARD_HTML


@app.get("/api/dashboard")
async def get_dashboard_data():
    """Get dashboard data"""
    return control_plane.get_dashboard_data()


@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None):
    """List training jobs"""
    data = control_plane.get_dashboard_data()
    jobs = data['jobs']
    
    if status:
        jobs = [j for j in jobs if j['status'] == status]
    
    return jobs


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get specific job details"""
    data = control_plane.get_dashboard_data()
    job = next((j for j in data['jobs'] if j['job_id'] == job_id), None)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@app.get("/api/clusters")
async def list_clusters(status: Optional[str] = None):
    """List GPU clusters"""
    data = control_plane.get_dashboard_data()
    clusters = data['clusters']
    
    if status:
        clusters = [c for c in clusters if c['status'] == status]
    
    return clusters


@app.get("/api/system/status")
async def get_system_status():
    """Get system status"""
    data = control_plane.get_dashboard_data()
    return data['system_status']


def main():
    """Run the dashboard server"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
