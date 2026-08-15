#!/bin/bash

# Fivoria AI Platform - VPS Deployment Script
# This script automates the complete setup and deployment on VPS
# Target: root@148.230.123.64
# Domain: fivoria.tech

set -e

echo "=========================================="
echo "Fivoria AI Platform - VPS Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="fivoria.tech"
REPO_URL="https://github.com/Fivoria/fivoria-ai-platform.git"
PROJECT_DIR="/opt/fivoria-ai-platform"
LOG_FILE="/var/log/fivoria-deployment.log"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a $LOG_FILE
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a $LOG_FILE
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root"
fi

log "Starting VPS deployment for Fivoria AI Platform"

# Update system
log "Updating system packages..."
apt-get update -y >> $LOG_FILE 2>&1 || error "Failed to update system"
apt-get upgrade -y >> $LOG_FILE 2>&1 || warning "System upgrade had issues"

# Install essential packages
log "Installing essential packages..."
apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    ufw \
    fail2ban \
    >> $LOG_FILE 2>&1 || error "Failed to install essential packages"

# Install Docker
log "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh >> $LOG_FILE 2>&1 || error "Failed to install Docker"
    systemctl enable docker
    systemctl start docker
    usermod -aG docker root
    log "Docker installed successfully"
else
    log "Docker is already installed"
    docker --version
fi

# Install Docker Compose
log "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    log "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log "Docker Compose installed successfully"
else
    log "Docker Compose is already installed"
    docker-compose --version
fi

# Install Kubernetes
log "Checking Kubernetes installation..."
if ! command -v kubectl &> /dev/null; then
    log "Installing Kubernetes components..."
    
    # Add Kubernetes repository
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list
    
    apt-get update -y >> $LOG_FILE 2>&1
    apt-get install -y kubelet kubeadm kubectl >> $LOG_FILE 2>&1 || error "Failed to install Kubernetes"
    apt-mark hold kubelet kubeadm kubectl
    
    log "Kubernetes installed successfully"
    kubectl version --client
else
    log "Kubernetes is already installed"
    kubectl version --client
fi

# Initialize Kubernetes cluster (single-node for VPS)
log "Checking Kubernetes cluster status..."
if ! kubectl cluster-info &> /dev/null; then
    log "Initializing Kubernetes single-node cluster..."
    kubeadm init --pod-network-cidr=10.244.0.0/16 >> $LOG_FILE 2>&1 || error "Failed to initialize Kubernetes cluster"
    
    # Configure kubectl for root user
    mkdir -p /root/.kube
    cp -i /etc/kubernetes/admin.conf /root/.kube/config
    chown $(id -u):$(id -g) /root/.kube/config
    
    # Install Calico CNI
    log "Installing Calico CNI..."
    kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/calico.yaml >> $LOG_FILE 2>&1 || warning "Calico installation had issues"
    
    # Remove taint from master node to allow pods
    kubectl taint nodes --all node-role.kubernetes.io/control-plane- >> $LOG_FILE 2>&1 || true
    
    log "Kubernetes cluster initialized successfully"
else
    log "Kubernetes cluster is already running"
    kubectl cluster-info
fi

# Clone repository
log "Cloning Fivoria AI Platform repository..."
if [ -d "$PROJECT_DIR" ]; then
    log "Project directory already exists, pulling latest changes..."
    cd $PROJECT_DIR
    git pull origin main >> $LOG_FILE 2>&1 || warning "Git pull had issues"
else
    log "Creating project directory and cloning repository..."
    mkdir -p $PROJECT_DIR
    git clone $REPO_URL $PROJECT_DIR >> $LOG_FILE 2>&1 || error "Failed to clone repository"
    cd $PROJECT_DIR
fi

# Create Python virtual environment
log "Setting up Python virtual environment..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
log "Installing Python dependencies..."
pip install --upgrade pip >> $LOG_FILE 2>&1
pip install -r requirements.txt >> $LOG_FILE 2>&1 || error "Failed to install Python dependencies"

# Install frontend dependencies
log "Installing frontend dependencies..."
cd $PROJECT_DIR/web-platform/frontend
npm install >> $LOG_FILE 2>&1 || error "Failed to install frontend dependencies"
cd $PROJECT_DIR

# Setup environment variables
log "Setting up environment variables..."
cat > $PROJECT_DIR/.env << EOF
# Database Configuration
DB_HOST=mysql
DB_PORT=3306
DB_NAME=fivoria_ai
DB_USER=fivoria_user
DB_PASSWORD=fivoria_secure_password_2024

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# JWT Configuration
JWT_SECRET=fivoria_jwt_secret_key_2024_secure
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Domain Configuration
DOMAIN=$DOMAIN
API_URL=https://api.$DOMAIN
FRONTEND_URL=https://$DOMAIN

# Model Configuration
MODEL_PATH=/models
CHECKPOINT_PATH=/checkpoints

# Security
ALLOWED_ORIGINS=https://$DOMAIN,https://api.$DOMAIN
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
EOF

# Setup database
log "Setting up database..."
cd $PROJECT_DIR/web-platform
python3 setup-database.py >> $LOG_FILE 2>&1 || warning "Database setup had issues"

# Build Docker images
log "Building Docker images..."
cd $PROJECT_DIR

# Build web API image
log "Building web API Docker image..."
docker build -f web-platform/docker/web-api.Dockerfile -t fivoria/web-api:latest -t fivoria/web-api:v1.0 . >> $LOG_FILE 2>&1 || error "Failed to build web API image"

# Build agent API image
log "Building agent API Docker image..."
docker build -f web-platform/docker/agent-api.Dockerfile -t fivoria/agent-api:latest -t fivoria/agent-api:v1.0 . >> $LOG_FILE 2>&1 || error "Failed to build agent API image"

# Build frontend image
log "Building frontend Docker image..."
docker build -f web-platform/docker/frontend.Dockerfile -t fivoria/frontend:latest -t fivoria/frontend:v1.0 . >> $LOG_FILE 2>&1 || error "Failed to build frontend image"

# Deploy with Docker Compose
log "Deploying services with Docker Compose..."
cd $PROJECT_DIR/web-platform
docker-compose down >> $LOG_FILE 2>&1 || true
docker-compose up -d >> $LOG_FILE 2>&1 || error "Failed to start services with Docker Compose"

# Wait for services to be healthy
log "Waiting for services to be healthy..."
sleep 30

# Check service status
log "Checking service status..."
docker-compose ps

# Deploy to Kubernetes
log "Deploying to Kubernetes..."
cd $PROJECT_DIR/web-platform/kubernetes

# Apply namespace
kubectl apply -f namespace.yaml >> $LOG_FILE 2>&1 || warning "Namespace creation had issues"

# Apply configurations
kubectl apply -f configmap.yaml >> $LOG_FILE 2>&1 || warning "Configmap creation had issues"
kubectl apply -f secret.yaml >> $LOG_FILE 2>&1 || warning "Secret creation had issues"

# Apply database
kubectl apply -f mysql-deployment.yaml >> $LOG_FILE 2>&1 || warning "MySQL deployment had issues"
kubectl apply -f mysql-service.yaml >> $LOG_FILE 2>&1 || warning "MySQL service had issues"

# Apply Redis
kubectl apply -f redis-deployment.yaml >> $LOG_FILE 2>&1 || warning "Redis deployment had issues"
kubectl apply -f redis-service.yaml >> $LOG_FILE 2>&1 || warning "Redis service had issues"

# Apply web services
kubectl apply -f web-api-deployment.yaml >> $LOG_FILE 2>&1 || warning "Web API deployment had issues"
kubectl apply -f web-api-service.yaml >> $LOG_FILE 2>&1 || warning "Web API service had issues"

kubectl apply -f agent-api-deployment.yaml >> $LOG_FILE 2>&1 || warning "Agent API deployment had issues"
kubectl apply -f agent-api-service.yaml >> $LOG_FILE 2>&1 || warning "Agent API service had issues"

kubectl apply -f frontend-deployment.yaml >> $LOG_FILE 2>&1 || warning "Frontend deployment had issues"
kubectl apply -f frontend-service.yaml >> $LOG_FILE 2>&1 || warning "Frontend service had issues"

# Apply ingress
kubectl apply -f ingress.yaml >> $LOG_FILE 2>&1 || warning "Ingress creation had issues"

# Wait for pods to be ready
log "Waiting for Kubernetes pods to be ready..."
kubectl wait --for=condition=ready pod -l app=fivoria -n fivoria --timeout=300s >> $LOG_FILE 2>&1 || warning "Some pods are not ready"

# Install and configure Nginx
log "Installing and configuring Nginx..."
apt-get install -y nginx >> $LOG_FILE 2>&1 || error "Failed to install Nginx"

# Install Certbot for SSL
log "Installing Certbot for SSL..."
apt-get install -y certbot python3-certbot-nginx >> $LOG_FILE 2>&1 || error "Failed to install Certbot"

# Configure Nginx for fivoria.tech
log "Configuring Nginx for $DOMAIN..."
cat > /etc/nginx/sites-available/fivoria.tech << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /agent {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/fivoria.tech /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t || error "Nginx configuration test failed"

# Restart Nginx
systemctl restart nginx
systemctl enable nginx

# Setup SSL with Certbot
log "Setting up SSL certificate for $DOMAIN..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN >> $LOG_FILE 2>&1 || warning "SSL setup had issues"

# Configure firewall
log "Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw allow 8001/tcp
ufw allow 3000/tcp
ufw --force enable

# Setup fail2ban
log "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
EOF

systemctl restart fail2ban
systemctl enable fail2ban

# Setup monitoring
log "Setting up basic monitoring..."
apt-get install -y prometheus node-exporter grafana >> $LOG_FILE 2>&1 || warning "Monitoring setup had issues"

# Create systemd services for auto-restart
log "Creating systemd services..."

# Web API service
cat > /etc/systemd/system/fivoria-web-api.service << EOF
[Unit]
Description=Fivoria Web API Service
After=network.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/web-platform/services/web-api
ExecStart=/usr/bin/docker-compose -f $PROJECT_DIR/web-platform/docker-compose.yml up web-api
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Agent API service
cat > /etc/systemd/system/fivoria-agent-api.service << EOF
[Unit]
Description=Fivoria Agent API Service
After=network.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/web-platform/services/agent-api
ExecStart=/usr/bin/docker-compose -f $PROJECT_DIR/web-platform/docker-compose.yml up agent-api
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Frontend service
cat > /etc/systemd/system/fivoria-frontend.service << EOF
[Unit]
Description=Fivoria Frontend Service
After=network.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/web-platform/frontend
ExecStart=/usr/bin/npm run dev
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable fivoria-web-api.service
systemctl enable fivoria-agent-api.service
systemctl enable fivoria-frontend.service

# Start services
systemctl start fivoria-web-api.service
systemctl start fivoria-agent-api.service
systemctl start fivoria-frontend.service

# Final status check
log "Performing final status check..."
sleep 10

echo "=========================================="
echo "Deployment Status Check"
echo "=========================================="

# Check Docker containers
echo -e "\n${GREEN}Docker Containers:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check Kubernetes pods
echo -e "\n${GREEN}Kubernetes Pods:${NC}"
kubectl get pods -n fivoria

# Check services
echo -e "\n${GREEN}System Services:${NC}"
systemctl status nginx | head -n 3
systemctl status docker | head -n 3

# Check Nginx
echo -e "\n${GREEN}Nginx Status:${NC}"
nginx -t

log "Deployment completed successfully!"
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo -e "Domain: ${GREEN}https://$DOMAIN${NC}"
echo -e "API: ${GREEN}https://api.$DOMAIN${NC}"
echo -e "Project Directory: $PROJECT_DIR"
echo -e "Logs: $LOG_FILE"
echo ""
echo "To check logs:"
echo "  Docker: docker logs -f <container_name>"
echo "  Kubernetes: kubectl logs -f <pod_name> -n fivoria"
echo "  Nginx: tail -f /var/log/nginx/access.log"
echo ""
echo "To manage services:"
echo "  Docker: docker-compose -f $PROJECT_DIR/web-platform/docker-compose.yml <command>"
echo "  Kubernetes: kubectl <command> -n fivoria"
echo "  Systemd: systemctl <command> fivoria-<service>"
echo "=========================================="

log "VPS deployment script completed successfully"
