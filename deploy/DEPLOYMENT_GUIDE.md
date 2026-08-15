# Fivoria AI Platform - VPS Deployment Guide

## Overview

This guide provides complete instructions for deploying the Fivoria AI Platform on your VPS (148.230.123.64) with the domain fivoria.tech.

## Prerequisites

- **VPS Access**: SSH access to root@148.230.123.64
- **Domain**: fivoria.tech with DNS configured to point to your VPS IP
- **System Requirements**:
  - Minimum 4GB RAM (8GB recommended)
  - 50GB disk space (100GB recommended)
  - Ubuntu 20.04+ or Debian 11+

## Quick Deployment (Automated)

The fastest way to deploy is using the automated deployment script:

```bash
# SSH into your VPS
ssh root@148.230.123.64

# Download and run the deployment script
wget https://raw.githubusercontent.com/Fivoria/fivoria-ai-platform/main/deploy/vps-setup.sh
chmod +x vps-setup.sh
./vps-setup.sh
```

The automated script will:
1. Update system packages
2. Install Docker and Docker Compose
3. Install Kubernetes (single-node cluster)
4. Clone the repository
5. Install all dependencies
6. Build Docker images
7. Deploy services with Docker Compose
8. Deploy to Kubernetes
9. Configure Nginx with SSL
10. Setup firewall and security
11. Configure monitoring

## Manual Deployment

If you prefer manual deployment or need to customize the setup:

### Step 1: System Preparation

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install essential packages
apt-get install -y curl wget git vim htop net-tools software-properties-common \
    apt-transport-https ca-certificates gnupg lsb-release python3 python3-pip \
    python3-venv nodejs npm ufw fail2ban
```

### Step 2: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### Step 3: Install Kubernetes

```bash
# Add Kubernetes repository
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list

apt-get update
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

# Initialize single-node cluster
kubeadm init --pod-network-cidr=10.244.0.0/16

# Configure kubectl
mkdir -p /root/.kube
cp -i /etc/kubernetes/admin.conf /root/.kube/config
chown $(id -u):$(id -g) /root/.kube/config

# Install Calico CNI
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/calico.yaml

# Remove taint from master node
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

### Step 4: Clone Repository

```bash
# Clone the repository
git clone https://github.com/Fivoria/fivoria-ai-platform.git /opt/fivoria-ai-platform
cd /opt/fivoria-ai-platform
```

### Step 5: Setup Environment

```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install frontend dependencies
cd web-platform/frontend
npm install
cd ../..
```

### Step 6: Configure Environment Variables

```bash
# Create .env file
cat > .env << EOF
# Database Configuration
DB_HOST=mysql
DB_PORT=3306
DB_NAME=fivoria_ai
DB_USER=fivoria_user
DB_PASSWORD=fivoria_secure_password_2024

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_secure_password_2024

# JWT Configuration
JWT_SECRET=fivoria_jwt_secret_key_2024_secure
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Domain Configuration
DOMAIN=fivoria.tech
API_URL=https://api.fivoria.tech
FRONTEND_URL=https://fivoria.tech

# Model Configuration
MODEL_PATH=/models
CHECKPOINT_PATH=/checkpoints

# Security
ALLOWED_ORIGINS=https://fivoria.tech,https://api.fivoria.tech
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
EOF
```

### Step 7: Setup Database

```bash
cd web-platform
python3 setup-database.py
cd ..
```

### Step 8: Build Docker Images

```bash
# Build web API image
docker build -f web-platform/docker/web-api.Dockerfile -t fivoria/web-api:latest .

# Build agent API image
docker build -f web-platform/docker/agent-api.Dockerfile -t fivoria/agent-api:latest .

# Build frontend image
docker build -f web-platform/docker/frontend.Dockerfile -t fivoria/frontend:latest .
```

### Step 9: Deploy with Docker Compose

```bash
cd web-platform
docker-compose up -d
```

### Step 10: Deploy to Kubernetes

```bash
cd kubernetes

# Apply namespace
kubectl apply -f namespace.yaml

# Apply configuration
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml

# Apply storage
kubectl apply -f mysql-pvc.yaml
kubectl apply -f redis-pvc.yaml
kubectl apply -f models-pvc.yaml
kubectl apply -f checkpoints-pvc.yaml

# Apply database
kubectl apply -f mysql-deployment.yaml
kubectl apply -f mysql-service.yaml

# Apply Redis
kubectl apply -f redis-deployment.yaml
kubectl apply -f redis-service.yaml

# Apply services
kubectl apply -f web-api-deployment.yaml
kubectl apply -f web-api-service.yaml
kubectl apply -f agent-api-deployment.yaml
kubectl apply -f agent-api-service.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml

# Apply autoscaling
kubectl apply -f horizontal-pod-autoscaler.yaml

# Apply ingress
kubectl apply -f ingress.yaml
```

### Step 11: Configure Nginx

```bash
# Install Nginx
apt-get install -y nginx

# Copy Nginx configuration
mkdir -p /etc/nginx/ssl
cp web-platform/nginx/nginx.conf /etc/nginx/nginx.conf

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx
systemctl enable nginx
```

### Step 12: Setup SSL Certificates

```bash
# Make SSL setup script executable
chmod +x web-platform/nginx/ssl-setup.sh

# Run SSL setup
./web-platform/nginx/ssl-setup.sh
```

### Step 13: Configure Firewall

```bash
# Configure UFW
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # Web API
ufw allow 8001/tcp  # Agent API
ufw allow 3000/tcp  # Frontend
ufw --force enable
```

### Step 14: Setup Monitoring

```bash
# Install monitoring tools
apt-get install -y prometheus node-exporter grafana

# Enable services
systemctl enable prometheus
systemctl enable node-exporter
systemctl enable grafana
systemctl start prometheus
systemctl start node-exporter
systemctl start grafana
```

## Verification

### Check Docker Containers

```bash
docker ps
```

Expected output:
- fivoria-mysql
- fivoria-redis
- fivoria-web-api
- fivoria-agent-api
- fivORIA-frontend

### Check Kubernetes Pods

```bash
kubectl get pods -n fivoria
```

Expected output:
- mysql-*
- redis-*
- web-api-*
- agent-api-*
- frontend-*

### Check Services

```bash
kubectl get services -n fivoria
```

### Check Nginx

```bash
nginx -t
systemctl status nginx
```

### Test Endpoints

```bash
# Test frontend
curl https://fivoria.tech

# Test web API
curl https://api.fivoria.tech/health

# Test agent API)
curl https://agent.fivoria.tech/health
```

## Management Commands

### Docker Management

```bash
# View logs
docker logs -f fivoria-web-api
docker logs -f fivoria-agent-api
docker logs -f fivoria-frontend

# Restart services
docker-compose restart web-api
docker-compose restart agent-api
docker-compose restart frontend

# Stop all services
docker-compose down

# Start all services
docker-compose up -d
```

### Kubernetes Management

```bash
# View logs
kubectl logs -f deployment/web-api -n fivoria
kubectl logs -f deployment/agent-api -n fivoria
kubectl logs -f deployment/frontend -n fivoria

# Restart deployments
kubectl rollout restart deployment/web-api -n fivoria
kubectl rollout restart deployment/agent-api -n fivoria
kubectl rollout restart deployment/frontend -n fivoria

# Scale deployments
kubectl scale deployment/web-api --replicas=5 -n fivoria
kubectl scale deployment/agent-api --replicas=3 -n fivoria

# Check pod status
kubectl get pods -n fivoria
kubectl describe pod <pod-name> -n fivoria
```

### Nginx Management

```bash
# Test configuration
nginx -t

# Reload configuration
nginx -s reload

# Restart Nginx
systemctl restart nginx

# View logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### SSL Certificate Management

```bash
# Renew certificates manually
certbot renew

# Check certificate status
certbot certificates

# Force renewal
certbot renew --force-renewal
```

## Troubleshooting

### Docker Issues

```bash
# Check Docker logs
journalctl -u docker

# Restart Docker
systemctl restart docker

# Clean up Docker resources
docker system prune -a
```

### Kubernetes Issues

```bash
# Check cluster status
kubectl cluster-info
kubectl get nodes

# Check pod logs
kubectl logs <pod-name> -n fivoria

# Describe pod for details
kubectl describe pod <pod-name> -n fivoria

# Delete stuck pods
kubectl delete pod <pod-name> -n fivoria --force --grace-period=0
```

### Database Issues

```bash
# Access MySQL
docker exec -it fivoria-mysql mysql -u fivoria_user -p fivoria_ai

# Check MySQL logs
docker logs fivoria-mysql

# Restart MySQL
docker-compose restart mysql
```

### Nginx Issues

```bash
# Check Nginx status
systemctl status nginx

# View error logs
tail -f /var/log/nginx/error.log

# Test configuration
nginx -t
```

### SSL Issues

```bash
# Check certificate expiration
openssl x509 -enddate -noout -in /etc/nginx/ssl/fullchain.pem

# Renew certificates
certbot renew --post-hook "systemctl reload nginx"
```

## Security Best Practices

1. **Change Default Passwords**: Update all default passwords in environment variables
2. **Regular Updates**: Keep system and packages updated
3. **Firewall Configuration**: Only open necessary ports
4. **SSL/TLS**: Ensure SSL certificates are valid and auto-renewal is configured
5. **Monitoring**: Monitor logs and system performance
6. **Backups**: Regular database and file backups
7. **Access Control**: Limit SSH access and use key-based authentication

## Performance Optimization

### Database Optimization

```bash
# MySQL tuning
# Edit /etc/mysql/my.cnf and add:
[mysqld]
innodb_buffer_pool_size = 1G
max_connections = 200
query_cache_size = 64M
```

### Nginx Optimization

The provided nginx.conf includes:
- Gzip compression
- Keep-alive connections
- Rate limiting
- Caching headers

### Kubernetes Resource Limits

Adjust resource limits in deployment YAMLs based on your VPS specifications.

## Backup Strategy

### Database Backup

```bash
# Create backup script
cat > /opt/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec fivoria-mysql mysqldump -u fivoria_user -pfivoria_secure_password_2024 fivoria_ai > /backup/fivoria_ai_$DATE.sql
find /backup -name "fivoria_ai_*.sql" -mtime +7 -delete
EOF

chmod +x /opt/backup-db.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup-db.sh") | crontab -
```

### File Backup

```bash
# Backup important directories
rsync -avz /opt/fivoria-ai-platform/ /backup/fivoria-ai-platform/
```

## Scaling

### Horizontal Scaling

Kubernetes HPA is configured for automatic scaling:

```bash
# Check HPA status
kubectl get hpa -n fivoria

# Manually scale
kubectl scale deployment web-api --replicas=5 -n fivoria
```

### Vertical Scaling

Update resource limits in deployment YAMLs:

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

## Monitoring

### System Monitoring

Access Grafana at `http://your-vps-ip:3000` (default credentials: admin/admin)

### Application Monitoring

```bash
# View Docker stats
docker stats

# View Kubernetes resource usage
kubectl top pods -n fivoria
kubectl top nodes
```

### Log Monitoring

```bash
# Docker logs
docker logs -f --tail=100 fivoria-web-api

# Kubernetes logs
kubectl logs -f deployment/web-api -n fivoria --tail=100

# Nginx logs
tail -f /var/log/nginx/access.log
```

## Support

For issues or questions:
- Check logs in `/var/log/fivoria-deployment.log`
- Review this deployment guide
- Check GitHub issues: https://github.com/Fivoria/fivoria-ai-platform/issues

## Summary

After completing the deployment, you will have:

- **Frontend**: https://fivoria.tech
- **Web API**: https://api.fivoria.tech
- **Agent API**: https://agent.fivoria.tech
- **Database**: MySQL 8.0
- **Cache**: Redis 7
- **Orchestration**: Kubernetes with auto-scaling
- **SSL**: Let's Encrypt certificates with auto-renewal
- **Monitoring**: Prometheus, Grafana, Node Exporter
- **Security**: Firewall, Fail2ban, rate limiting

The system is production-ready and will automatically handle scaling, SSL renewal, and monitoring.
