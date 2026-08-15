#!/bin/bash

# SSL Certificate Setup Script for Fivoria AI Platform
# This script sets up SSL certificates using Let's Encrypt

set -e

DOMAIN="fivoria.tech"
EMAIL="admin@fivoria.tech"
NGINX_SSL_DIR="/etc/nginx/ssl"
CERTBOT_WEBROOT="/var/www/certbot"

echo "Setting up SSL certificates for $DOMAIN"

# Create necessary directories
mkdir -p $NGINX_SSL_DIR
mkdir -p $CERTBOT_WEBROOT

# Install Certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Obtain SSL certificate for all domains
echo "Obtaining SSL certificates..."
certbot certonly --webroot \
    --webroot-path=$CERTBOT_WEBROOT \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN \
    -d api.$DOMAIN \
    -d agent.$DOMAIN

# Copy certificates to nginx ssl directory
echo "Copying certificates to nginx SSL directory..."
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $NGINX_SSL_DIR/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $NGINX_SSL_DIR/
cp /etc/letsencrypt/live/$DOMAIN/chain.pem $NGINX_SSL_DIR/

# Set proper permissions
chmod 644 $NGINX_SSL_DIR/fullchain.pem
chmod 644 $NGINX_SSL_DIR/chain.pem
chmod 600 $NGINX_SSL_DIR/privkey.pem

# Setup auto-renewal
echo "Setting up certificate auto-renewal..."
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

# Reload nginx
echo "Reloading nginx..."
systemctl reload nginx

echo "SSL certificates setup completed successfully!"
echo "Certificates will auto-renew daily at 3 AM"
