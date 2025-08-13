#!/bin/bash

# Quick EC2 Setup Script for TO7FA Backend
# Run this script first on your EC2 instance before running deploy.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}TO7FA Backend - EC2 Quick Setup${NC}"
echo "This script will prepare your EC2 instance for TO7FA deployment"
echo ""

# Update system
echo -e "${GREEN}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo -e "${GREEN}Installing essential packages...${NC}"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    mysql-server \
    libmysqlclient-dev \
    nginx \
    git \
    curl \
    htop \
    nano \
    ufw \
    unzip

# Secure MySQL installation
echo -e "${GREEN}Securing MySQL installation...${NC}"
sudo mysql_secure_installation

# Enable and start services
echo -e "${GREEN}Enabling services...${NC}"
sudo systemctl enable mysql
sudo systemctl enable nginx
sudo systemctl start mysql
sudo systemctl start nginx

# Configure firewall
echo -e "${GREEN}Configuring firewall...${NC}"
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Create project directories
echo -e "${GREEN}Creating project directories...${NC}"
sudo mkdir -p /var/www/to7fa
sudo mkdir -p /var/log/to7fa
sudo mkdir -p /var/run/to7fa
sudo chown -R ubuntu:ubuntu /var/www/to7fa
sudo chown -R ubuntu:ubuntu /var/log/to7fa
sudo chown -R ubuntu:ubuntu /var/run/to7fa

echo -e "${GREEN}EC2 setup completed!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Upload your TO7FA code to this instance"
echo "2. Run the deploy.sh script from your project directory"
echo "3. Follow the deployment guide for configuration"
echo ""
echo -e "${GREEN}Ready for TO7FA deployment!${NC}"