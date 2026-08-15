# Fivoria AI Web Platform - Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for production deployment)
- kubectl configured
- Domain name for production

## Development Deployment

### Using Docker Compose

1. Build and start all services:
```bash
cd web-platform/docker
docker-compose up -d
```

2. Access services:
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Web API: http://localhost:8001
- Agent API: http://localhost:8002
- Project Service: http://localhost:8003
- Model Gateway: http://localhost:8004
- Preview Service: http://localhost:8005
- Monitoring: http://localhost:8006

3. View logs:
```bash
docker-compose logs -f frontend
docker-compose logs -f web-api
```

4. Stop services:
```bash
docker-compose down
```

## Production Deployment

### Kubernetes Deployment

1. Create namespace:
```bash
kubectl apply -f kubernetes/namespaces/namespace.yaml
```

2. Apply configurations:
```bash
kubectl apply -f kubernetes/configmaps/config.yaml
kubectl apply -f kubernetes/secrets/secrets.yaml
```

3. Update secrets with actual values:
```bash
kubectl edit secret fivoria-secrets -n fivoria
```

4. Create persistent volume claim:
```bash
kubectl apply -f kubernetes/pvc/workspaces-pvc.yaml
```

5. Deploy services:
```bash
kubectl apply -f kubernetes/deployments/
kubectl apply -f kubernetes/services/
```

6. Configure ingress:
```bash
kubectl apply -f kubernetes/ingress/ingress.yaml
```

7. Verify deployment:
```bash
kubectl get pods -n fivoria
kubectl get services -n fivoria
```

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=https://api.fivoria.example.com
NEXT_PUBLIC_WS_URL=https://agent-api.fivoria.example.com
NEXT_PUBLIC_MODEL_GATEWAY_URL=https://model-gateway.fivoria.example.com
```

### Backend Services
- DATABASE_URL: MySQL connection string
- REDIS_URL: Redis connection string
- JWT_SECRET: JWT signing secret
- API_KEY_ENCRYPTION_KEY: API key encryption key

## Monitoring

### Prometheus Metrics
Access metrics at: http://monitoring-service:8006/metrics

Key metrics:
- API request rate and duration
- Agent task execution
- Model inference requests
- Active users and projects

### Health Checks
All services expose `/health` endpoint for health checks.

## Scaling

### Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fivoria-web-api-hpa
  namespace: fivoria
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fivoria-web-api
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## Security

- All services run behind API Gateway
- JWT authentication required for all endpoints
- RBAC for authorization
- Rate limiting enabled
- Secrets managed via Kubernetes Secrets

## Backup

### Database Backup
```bash
kubectl exec -n fivoria mysql-0 -- mysqldump -u fivoria -p fivoria > backup.sql
```

### Workspace Backup
```bash
kubectl exec -n fivoria project-service-0 -- tar -czf /backup/workspaces.tar.gz /tmp/fivoria-workspaces
```

## Troubleshooting

### Service not starting
```bash
kubectl logs -n fivoria <pod-name>
kubectl describe pod -n fivoria <pod-name>
```

### Database connection issues
```bash
kubectl exec -n fivoria mysql-0 -- mysql -u fivoria -p
```

### Redis connection issues
```bash
kubectl exec -n fivoria redis-0 -- redis-cli ping
```
