#!/bin/bash
# 🚀 TO7FA Backend Quick Setup Script
# Run this script on a new server to set up the TO7FA backend

set -e  # Exit on any error

echo "🚀 TO7FA Backend Setup Script"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root"
    exit 1
fi

print_status "Starting TO7FA Backend setup..."

# 1. Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install required system packages
print_status "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv mysql-server mysql-client libmysqlclient-dev build-essential pkg-config

# 3. Start and enable MySQL
print_status "Starting MySQL service..."
sudo systemctl start mysql
sudo systemctl enable mysql

# 4. Create virtual environment
print_status "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# 5. Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Database setup
print_status "Setting up database..."
echo ""
print_warning "DATABASE SETUP REQUIRED!"
echo "Please run these MySQL commands manually:"
echo ""
echo -e "${YELLOW}mysql -u root -p${NC}"
echo ""
echo "Then execute these SQL commands:"
echo -e "${BLUE}CREATE DATABASE to7fa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;${NC}"
echo -e "${BLUE}CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'your_strong_password_here';${NC}"
echo -e "${BLUE}GRANT ALL PRIVILEGES ON to7fa_db.* TO 'django_user'@'localhost';${NC}"
echo -e "${BLUE}FLUSH PRIVILEGES;${NC}"
echo -e "${BLUE}EXIT;${NC}"
echo ""
read -p "Press Enter after completing database setup..."

# 7. Update settings.py
print_status "Checking Django settings..."
if grep -q "django-insecure-" to7fabackend/settings.py; then
    print_error "❌ SECURITY: Default SECRET_KEY detected!"
    print_warning "Please update the SECRET_KEY in to7fabackend/settings.py"
    print_warning "Generate a new one at: https://djecrety.ir/"
fi

if grep -q "DEBUG = True" to7fabackend/settings.py; then
    print_warning "⚠️ DEBUG mode is enabled. Set DEBUG = False for production"
fi

# 8. Test database connection
print_status "Testing database connection..."
if python manage.py dbshell --command="SELECT 1;" > /dev/null 2>&1; then
    print_success "Database connection successful"
else
    print_error "Database connection failed. Please check your database settings."
    exit 1
fi

# 9. Run migrations
print_status "Running database migrations..."
python manage.py migrate

# 10. Create superuser
print_status "Creating Django superuser..."
echo ""
print_warning "Please create an admin account:"
python manage.py createsuperuser

# 11. Test the server
print_status "Testing Django server..."
python manage.py check

print_success "✅ Setup completed successfully!"
echo ""
echo "🎉 Your TO7FA backend is ready!"
echo ""
echo "Next steps:"
echo "1. Start the development server: python manage.py runserver 0.0.0.0:8000"
echo "2. Access Django Admin: http://your-ip:8000/admin/"
echo "3. Access TO7FA Admin Panel: http://your-ip:8000/dashboard/"
echo "4. Test Contact API: http://your-ip:8000/api/support/contact/create/"
echo ""
echo "📖 For production deployment, see DEPLOYMENT_GUIDE.md"
echo ""
print_warning "IMPORTANT: Update these settings in to7fabackend/settings.py:"
echo "  - SECRET_KEY (generate new one)"
echo "  - ALLOWED_HOSTS (add your domain/IP)"
echo "  - DEBUG = False (for production)"
echo "  - Database credentials"