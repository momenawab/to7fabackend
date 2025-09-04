# 🚀 TO7FA Backend Deployment Guide

Complete guide for deploying the TO7FA Django backend on a new device/server.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Environment Variables](#environment-variables)
4. [Installation Steps](#installation-steps)
5. [Database Migration](#database-migration)
6. [Admin Panel Setup](#admin-panel-setup)
7. [Production Configuration](#production-configuration)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### System Requirements
- **Python**: 3.8+ (recommended 3.10+)
- **MySQL**: 5.7+ or 8.0+
- **Operating System**: Linux (Ubuntu/CentOS), macOS, or Windows
- **Memory**: Minimum 2GB RAM
- **Storage**: Minimum 10GB free space

### Required Software
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv mysql-server mysql-client libmysqlclient-dev

# CentOS/RHEL
sudo yum install python3 python3-pip mysql-server mysql-devel

# macOS (using Homebrew)
brew install python mysql

# Windows
# Download Python from python.org
# Download MySQL from mysql.com
```

---

## 🗄️ Database Setup

### 1. MySQL Installation & Configuration

#### Start MySQL Service
```bash
# Linux
sudo systemctl start mysql
sudo systemctl enable mysql

# macOS
brew services start mysql

# Windows
# Use MySQL Workbench or Command Prompt as Administrator
```

#### Secure MySQL Installation
```bash
sudo mysql_secure_installation
```

### 2. Create Database and User

#### Login to MySQL
```bash
mysql -u root -p
```

#### Create Database and User
```sql
-- Create database
CREATE DATABASE to7fa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (CHANGE THESE CREDENTIALS!)
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'your_strong_password_here';

-- Grant permissions
GRANT ALL PRIVILEGES ON to7fa_db.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;

-- Verify creation
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User = 'django_user';

-- Exit
EXIT;
```

#### Test Database Connection
```bash
mysql -u django_user -p to7fa_db
```

---

## 🔐 Environment Variables

### 1. Database Configuration
**CRITICAL**: Update these values in `settings.py` or create a `.env` file:

```python
# to7fabackend/settings.py - Database Section
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'to7fa_db',                    # Database name
        'USER': 'django_user',                 # MySQL username
        'PASSWORD': 'your_strong_password_here', # MySQL password
        'HOST': 'localhost',                    # Database host
        'PORT': '3306',                        # MySQL port
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
```

### 2. Security Configuration
**IMPORTANT**: Change these settings:

```python
# Generate new secret key: https://djecrety.ir/
SECRET_KEY = 'your-new-secret-key-here-make-it-very-long-and-random'

# Production settings
DEBUG = False  # Set to False in production
ALLOWED_HOSTS = ['your-domain.com', 'your-ip-address', 'localhost']

# CORS settings (if serving Flutter app from different domain)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend-domain.com",
]
```

### 3. Optional: Environment File (.env)
Create a `.env` file in the project root:

```bash
# Database
DB_NAME=to7fa_db
DB_USER=django_user
DB_PASSWORD=your_strong_password_here
DB_HOST=localhost
DB_PORT=3306

# Security
SECRET_KEY=your-new-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-ip-address

# Email (if using email features)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

Then update settings.py to use environment variables:
```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

---

## 📦 Installation Steps

### 1. Clone/Copy Project
```bash
# If using Git
git clone <repository-url>
cd TO7FAA/to7fabackend

# Or extract from ZIP file
unzip TO7FAA-backend.zip
cd TO7FAA/to7fabackend
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# If mysqlclient fails to install:
# Ubuntu/Debian:
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
# CentOS/RHEL:
sudo yum install python3-devel mysql-devel gcc

# Then retry:
pip install mysqlclient
```

### 4. Update Configuration
```bash
# Edit database settings
nano to7fabackend/settings.py

# Update the DATABASES section with your MySQL credentials
# Update SECRET_KEY
# Update ALLOWED_HOSTS
# Set DEBUG = False for production
```

---

## 🗃️ Database Migration

### 1. Test Database Connection
```bash
python manage.py dbshell
# Should connect to MySQL without errors
# Type 'exit' to leave
```

### 2. Run Migrations
```bash
# Apply all migrations (creates tables)
python manage.py migrate

# Verify migration status
python manage.py showmigrations
```

### 3. Create Superuser
```bash
# Create admin account for Django admin
python manage.py createsuperuser

# Follow prompts to create:
# - Username
# - Email address
# - Password (will be hidden when typing)
```

### 4. Collect Static Files (Production)
```bash
# Only needed for production deployment
python manage.py collectstatic
```

---

## 👨‍💼 Admin Panel Setup

### 1. Access Django Admin
```bash
# Start development server
python manage.py runserver 0.0.0.0:8000

# Visit: http://your-ip:8000/admin/
# Login with superuser credentials
```

### 2. Access TO7FA Admin Panel
```bash
# Visit: http://your-ip:8000/dashboard/
# Login with superuser credentials

# Features available:
# - User Management
# - Product Management  
# - Order Management
# - Contact Requests (/dashboard/support-contacts/)
# - Analytics & Reports
```

### 3. Test Contact System
```bash
# Test contact creation API
curl -X POST http://your-ip:8000/api/support/contact/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "phone": "01234567890", 
    "subject": "Test Contact",
    "message": "Testing deployment"
  }'

# Should return success response with contact number
```

---

## 🚀 Production Configuration

### 1. Web Server Setup (Nginx + Gunicorn)

#### Install Gunicorn
```bash
pip install gunicorn
```

#### Create Gunicorn Service
```bash
# /etc/systemd/system/to7fa-backend.service
[Unit]
Description=TO7FA Django Backend
After=network.target

[Service]
User=your-username
Group=www-data
WorkingDirectory=/path/to/TO7FAA/to7fabackend
Environment="PATH=/path/to/TO7FAA/to7fabackend/venv/bin"
ExecStart=/path/to/TO7FAA/to7fabackend/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/path/to/TO7FAA/to7fabackend/to7fa.sock \
          to7fabackend.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/to7fa-backend
server {
    listen 80;
    server_name your-domain.com your-ip-address;

    location /static/ {
        alias /path/to/TO7FAA/to7fabackend/staticfiles/;
    }

    location /media/ {
        alias /path/to/TO7FAA/to7fabackend/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/TO7FAA/to7fabackend/to7fa.sock;
    }
}
```

#### Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl start to7fa-backend
sudo systemctl enable to7fa-backend

sudo ln -s /etc/nginx/sites-available/to7fa-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 2. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. MySQL Connection Errors
```bash
# Error: "Can't connect to MySQL server"
# Solution: Check MySQL service status
sudo systemctl status mysql
sudo systemctl start mysql

# Error: "Access denied for user"
# Solution: Verify user credentials
mysql -u django_user -p
```

#### 2. Migration Errors
```bash
# Error: "table already exists"
# Solution: Check migration status
python manage.py showmigrations
python manage.py migrate --fake-initial

# Error: "Unknown column"
# Solution: Reset migrations (CAUTION: Data loss)
python manage.py migrate support zero
python manage.py migrate support
```

#### 3. Permission Errors
```bash
# Error: "Permission denied"
# Solution: Fix file permissions
sudo chown -R www-data:www-data /path/to/TO7FAA/to7fabackend
sudo chmod -R 755 /path/to/TO7FAA/to7fabackend
```

#### 4. Import Errors
```bash
# Error: "No module named 'mysqlclient'"
# Solution: Install system dependencies
sudo apt-get install python3-dev default-libmysqlclient-dev
pip install mysqlclient
```

---

## 📊 Database Schema Overview

The system creates these main tables:
- **Users & Authentication**: `custom_auth_*` tables
- **Products**: `products_*` tables  
- **Orders**: `orders_*` tables
- **Contact System**: `support_contactrequest`, `support_contactnote`, `support_contactstats`
- **Admin Panel**: `admin_panel_*` tables
- **Notifications**: `notifications_*` tables
- **Wallet & Payments**: `wallet_*`, `payment_*` tables

---

## ✅ Deployment Checklist

- [ ] MySQL installed and running
- [ ] Database and user created with correct permissions
- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All requirements installed successfully
- [ ] Database settings updated in settings.py
- [ ] SECRET_KEY changed
- [ ] ALLOWED_HOSTS updated
- [ ] DEBUG set to False (production)
- [ ] Migrations applied successfully
- [ ] Superuser created
- [ ] Admin panel accessible
- [ ] Contact API tested
- [ ] Static files collected (production)
- [ ] Web server configured (production)
- [ ] SSL certificate installed (production)

---

## 🆘 Support

If you encounter issues:

1. **Check Logs**:
   ```bash
   # Django logs
   python manage.py runserver --verbosity=2
   
   # System logs
   sudo journalctl -u to7fa-backend -f
   
   # Nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Database Issues**: Verify MySQL connection and user permissions
3. **Import Errors**: Ensure all system dependencies are installed
4. **Permission Issues**: Check file ownership and permissions

---

📝 **Note**: Always backup your database before making changes in production!

```bash
# Backup database
mysqldump -u django_user -p to7fa_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
mysql -u django_user -p to7fa_db < backup_20241204_143022.sql
```