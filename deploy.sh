#!/bin/bash

# TO7FA Backend Deployment Script for EC2
# This script automates the deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="to7fa"
PROJECT_DIR="/var/www/to7fa"
VENV_DIR="/var/www/to7fa/venv"
REPO_URL="https://github.com/yourusername/TO7FAA.git"  # Update this with your actual repository
BRANCH="main"
USER="ubuntu"  # EC2 default user

echo -e "${GREEN}Starting TO7FA Backend Deployment...${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root. Run as ubuntu user with sudo privileges."
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
print_status "Installing system dependencies..."
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
    supervisor \
    ufw

# Install Gunicorn globally
print_status "Installing Gunicorn..."
sudo pip3 install gunicorn

# Create project directory
print_status "Creating project directory..."
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# Clone or update repository
if [ -d "$PROJECT_DIR/.git" ]; then
    print_status "Updating existing repository..."
    cd $PROJECT_DIR
    git pull origin $BRANCH
else
    print_status "Cloning repository..."
    git clone $REPO_URL $PROJECT_DIR
    cd $PROJECT_DIR
    git checkout $BRANCH
fi

# Navigate to backend directory
cd $PROJECT_DIR/to7fabackend

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv $VENV_DIR

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup MySQL database
print_status "Setting up MySQL database..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS to7fa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'strongpass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON to7fa_db.* TO 'django_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cp env_template .env
    print_warning "Please edit .env file with your actual configuration values!"
fi

# Create directories for static files, media, and logs
print_status "Creating necessary directories..."
sudo mkdir -p /var/www/to7fa/static
sudo mkdir -p /var/www/to7fa/media
sudo mkdir -p /var/log/to7fa
sudo chown -R $USER:www-data /var/www/to7fa
sudo chown -R $USER:$USER /var/log/to7fa
sudo chmod -R 755 /var/www/to7fa
sudo chmod -R 755 /var/log/to7fa

# Run Django migrations
print_status "Running Django migrations..."
source $VENV_DIR/bin/activate
export DJANGO_SETTINGS_MODULE=to7fabackend.settings_production
python manage.py migrate

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser (optional)
print_status "Would you like to create a superuser? (y/n)"
read -r response
if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
    python manage.py createsuperuser
fi

print_status "Deployment completed successfully!"
print_warning "Next steps:"
print_warning "1. Edit /var/www/to7fa/to7fabackend/.env with your actual configuration"
print_warning "2. Configure Nginx (run: sudo cp nginx.conf /etc/nginx/sites-available/to7fa)"
print_warning "3. Enable the site (run: sudo ln -s /etc/nginx/sites-available/to7fa /etc/nginx/sites-enabled/)"
print_warning "4. Configure systemd service (run: sudo cp to7fa.service /etc/systemd/system/)"
print_warning "5. Start services (run: sudo systemctl enable to7fa && sudo systemctl start to7fa)"
print_warning "6. Restart Nginx (run: sudo systemctl restart nginx)"
print_warning "7. Configure firewall (run: sudo ufw allow 80 && sudo ufw allow 443)"

echo -e "${GREEN}Deployment script completed!${NC}"