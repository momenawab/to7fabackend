# TO7FA E-Commerce Backend

<div align="center">

![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![CI/CD](https://img.shields.io/badge/CI%2FCD-Jenkins%20%7C%20GitHub%20Actions-orange)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?logo=redis&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-1.25-009639?logo=nginx&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-FCM-FFCA28?logo=firebase&logoColor=black)

**Production-ready Django REST API backend for Flutter mobile application with complete DevOps infrastructure**

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) • [Deployment](#deployment) • [CI/CD](#cicd-pipelines)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Docker Setup](#docker-setup)
- [CI/CD Pipelines](#cicd-pipelines)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**TO7FA Backend** is a production-grade REST API backend for the **TO7FA Flutter mobile application** - a comprehensive Arabic e-commerce marketplace.

This backend powers a full-featured Flutter app that includes shopping, seller registration, wallet system, AR product preview, and real-time notifications. The mobile app connects to this Django REST API to provide users with a seamless marketplace experience.

**🔗 Flutter App Repository**: [TO7FAA Mobile App](https://github.com/momenawab/TO7FAA) *(Update with your repo link)*

### Key Highlights

- ✅ **Flutter Mobile App Backend**: Powers iOS/Android app with REST APIs
- ✅ **Complete E-Commerce System**: Products, orders, cart, payments, wallet
- ✅ **Multi-Tenant Architecture**: Separate public API and admin panel containers
- ✅ **Real-time Features**: WebSocket support for live updates via Django Channels
- ✅ **Push Notifications**: Firebase Cloud Messaging for mobile notifications
- ✅ **AR Product Preview**: Backend support for 3D product visualization
- ✅ **Seller Dashboard**: API endpoints for seller registration and management
- ✅ **Production-Ready DevOps**: Docker, CI/CD, monitoring, health checks
- ✅ **Scalable Infrastructure**: Load balancing, caching, database optimization

**Live API**: [http://YOUR-DOMAIN/api](http://YOUR-DOMAIN/api)
**Admin Panel**: [http://admin.YOUR-DOMAIN/dashboard](http://admin.YOUR-DOMAIN/dashboard)

> **Note for Recruiters**: This is a complete, production-deployed project built to demonstrate full-stack and DevOps capabilities. Feel free to explore the codebase and documentation to assess technical skills.

---

## 📱 Mobile App Integration

This backend is specifically designed to serve the **TO7FA Flutter mobile application**. The Flutter app includes:

- **E-Commerce Features**: Browse products, add to cart, checkout, order tracking
- **User Authentication**: Registration, login, profile management
- **Seller Portal**: Multi-step seller registration with ID upload and verification
- **Wallet System**: In-app credits, transactions, refunds
- **AR Product Preview**: Augmented reality product visualization using camera
- **Push Notifications**: Real-time order updates and promotional messages
- **WhatsApp Integration**: Contact sellers directly via WhatsApp
- **Google Maps**: Location-based features for shipping addresses
- **Real-time Updates**: WebSocket connection for live notifications

The Flutter app communicates with this backend via RESTful APIs defined in `/lib/core/services/` and configured through `/lib/core/config/api_config.dart`.

---

## ⚡ Features

### Core API Features (Flutter App Backend)
- 🛒 **Shopping Cart & Orders** - Full cart management and order processing APIs
- 💳 **Payment Integration** - Secure payment gateway integration for mobile payments
- 👛 **Wallet System** - User wallet for credits and transactions (Flutter UI)
- 🔐 **Custom Authentication** - Token-based auth for mobile app sessions
- 📦 **Product Management** - CRUD operations, categories, inventory with image uploads
- 📱 **Push Notifications** - Firebase Cloud Messaging for iOS/Android notifications
- 🎨 **AR Product Support** - Media endpoints for 3D product visualization
- 👥 **Seller Registration API** - Multi-step seller onboarding with document upload
- 💬 **Support System** - Customer support ticketing (WhatsApp integration on mobile)
- 📊 **Admin Dashboard** - Comprehensive admin panel (separate from mobile app)
- ❓ **FAQ System** - Dynamic FAQ management accessible via Flutter app
- 🌐 **WebSocket Notifications** - Real-time updates for order status changes

### DevOps & Infrastructure
- 🐳 **Docker Containerization** - Multi-stage builds, optimized images
- 🚀 **CI/CD Pipelines** - Jenkins & GitHub Actions
- 🌐 **Nginx Reverse Proxy** - Load balancing, SSL termination
- 📊 **Health Monitoring** - Kubernetes-ready health checks
- 🔄 **Auto-Deployment** - Push-to-deploy workflows
- 🔒 **Security Best Practices** - Environment-based secrets, non-root containers

---

## 🛠️ Tech Stack

### Backend (API Server)
- **Framework**: Django 4.2 + Django REST Framework 3.14
- **Language**: Python 3.12
- **Database**: MySQL 8.0
- **Cache**: Redis 7.0
- **WebSockets**: Django Channels 4.0
- **ASGI Server**: Uvicorn (for WebSocket support)
- **WSGI Server**: Gunicorn (alternative)

### Mobile App (Client)
- **Framework**: Flutter 3.x
- **Language**: Dart 3.7.2
- **State Management**: GetX
- **HTTP Client**: http package
- **Storage**: get_storage
- **Notifications**: firebase_messaging, flutter_local_notifications
- **Maps**: google_maps_flutter, geolocator
- **AR Features**: camera, sensors_plus
- **WebSocket**: web_socket_channel

### DevOps & Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx 1.25 (load balancing)
- **CI/CD**: Jenkins, GitHub Actions
- **Cloud**: AWS EC2
- **Domain**: Namecheap DNS (YOUR-DOMAIN)
- **Registry**: Docker Hub

### Third-Party Integrations
- **Push Notifications**: Firebase Cloud Messaging (FCM) for iOS/Android
- **Storage**: Local media files (S3-ready for production scaling)
- **WhatsApp**: URL scheme integration for seller contact

---

## 🏗️ Architecture

### Full System Architecture (Mobile + Backend)

```
┌──────────────────────────────────────────────────────────────┐
│               Flutter Mobile App (iOS/Android)               │
│  - GetX State Management                                     │
│  - HTTP REST API Calls                                       │
│  - WebSocket Real-time Updates                              │
│  - Firebase Push Notifications                              │
└────────────┬─────────────────────────────────────────────────┘
             │ HTTPS/WSS
             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Internet Traffic                        │
│                    Domain: YOUR-DOMAIN                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Nginx (Port 80)    │
              │  Reverse Proxy       │
              │  Load Balancer       │
              │  SSL Termination     │
              └──────────┬───────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
│ Django Public   │ │ Django      │ │ Django       │
│ API (×3)        │ │ Admin (×2)  │ │ Static Files │
│ /api/*          │ │ /dashboard  │ │ Media Files  │
│ Port 8000       │ │ Port 8001   │ │              │
└────────┬────────┘ └──────┬──────┘ └──────────────┘
         │                 │
         └────────┬────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│ MySQL   │  │ Redis   │  │ Media    │
│ 8.0     │  │ Cache   │  │ Storage  │
│ Products│  │ Sessions│  │ Images   │
│ Orders  │  │ WebSocket│ │ Documents│
└─────────┘  └─────────┘  └──────────┘
```

### Container Architecture

**Development** (4 containers):
```
┌──────────────┐    ┌──────────┐
│   Django     │───▶│  MySQL   │
└──────┬───────┘    └──────────┘
       │
       └──────────▶ ┌──────────┐
                    │  Redis   │
                    └──────────┘
┌──────────────┐
│    Nginx     │───▶ Django
└──────────────┘
```

**Production** (7 containers):
- 3× Django Public API (scaled)
- 2× Django Admin Panel (scaled)
- 1× MySQL
- 1× Redis
- 1× Nginx Load Balancer

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/momenawab/to7fabackend.git
   cd to7fabackend
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Start development containers:**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations:**
   ```bash
   docker-compose exec django python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   docker-compose exec django python manage.py createsuperuser
   ```

6. **Access the application:**
   - API: http://localhost/api/
   - Admin: http://localhost/admin/
   - Health: http://localhost/health/

### Production Deployment

See [Deployment Guide](#deployment) for EC2 deployment instructions.

---

## 📁 Project Structure

### Backend (Django API - This Repository)
```
to7fabackend/
├── admin_panel/          # Admin dashboard app (web-based)
├── cart/                 # Shopping cart API endpoints
├── custom_auth/          # Custom authentication (token-based for mobile)
├── faq/                  # FAQ management API
├── notifications/        # Push notification system (FCM integration)
├── orders/               # Order processing API
├── payment/              # Payment gateway integration
├── products/             # Product catalog API with image upload
├── support/              # Customer support API
├── wallet/               # User wallet system API
├── to7fabackend/         # Django settings & config
│   ├── settings.py       # Environment-based settings
│   ├── urls.py
│   ├── asgi.py          # ASGI config (Channels for WebSocket)
│   └── wsgi.py
├── nginx/                # Nginx configurations
│   ├── nginx.conf        # Development config
│   └── nginx.production.conf
├── docs/                 # Documentation
│   ├── JENKINS_SETUP.md
│   ├── CICD_COMPARISON.md
│   └── CICD_GITHUB_ACTIONS.md
├── .github/workflows/    # GitHub Actions CI/CD
│   └── deploy.yml
├── jenkins/              # Jenkins setup files
├── Dockerfile            # Multi-stage production build
├── docker-compose.yml    # Development setup
├── docker-compose.production.yml  # Production setup
├── Jenkinsfile           # Jenkins pipeline
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── .dockerignore
└── README.md
```

### Mobile App (Flutter - Separate Repository)
```
TO7FAA/                   # Flutter mobile app
├── lib/
│   ├── core/
│   │   ├── services/     # API service layer
│   │   │   ├── auth_service.dart
│   │   │   ├── product_service.dart
│   │   │   ├── cart_service.dart
│   │   │   ├── order_service.dart
│   │   │   └── websocket_service.dart
│   │   ├── config/
│   │   │   └── api_config.dart    # Backend API URL configuration
│   │   └── models/       # Data models matching Django API
│   ├── features/
│   │   ├── account/      # Authentication & user profile
│   │   ├── home/         # Product browsing
│   │   ├── products/     # Product details, AR preview
│   │   ├── seller/       # Seller registration
│   │   ├── wallet/       # Wallet management
│   │   └── notifications/# Push notifications
│   └── main.dart
├── android/              # Android platform code
├── ios/                  # iOS platform code
└── pubspec.yaml          # Flutter dependencies
```

---

## 📚 API Documentation

### Main Endpoints (Used by Flutter App)

#### Authentication
```http
POST /api/auth/register/      # User registration
POST /api/auth/login/         # User login
POST /api/auth/logout/        # User logout
GET  /api/auth/profile/       # Get user profile
```

#### Products
```http
GET    /api/products/         # List all products
GET    /api/products/{id}/    # Get product details
POST   /api/products/         # Create product (admin)
PUT    /api/products/{id}/    # Update product (admin)
DELETE /api/products/{id}/    # Delete product (admin)
```

#### Cart
```http
GET    /api/cart/             # Get user cart
POST   /api/cart/add/         # Add item to cart
PUT    /api/cart/update/      # Update cart item
DELETE /api/cart/remove/{id}/ # Remove from cart
```

#### Orders
```http
GET    /api/orders/           # List user orders
POST   /api/orders/create/    # Create order
GET    /api/orders/{id}/      # Get order details
```

#### Notifications (Flutter Integration)
```http
GET    /api/notifications/                    # Get user notifications
POST   /api/notifications/register-device/    # Register FCM token from Flutter app
POST   /api/notifications/mark-read/{id}/     # Mark notification as read
```

**Flutter Service**: `lib/core/services/notification_service.dart`

#### Seller Registration (Flutter Multi-Step Form)
```http
POST   /api/seller/register/                  # Submit seller application
GET    /api/seller/status/                    # Check application status
POST   /api/seller/upload-document/           # Upload ID/documents
```

**Flutter Pages**: `lib/features/account/presentation/pages/seller_registration_steps/`

#### WebSocket (Real-time Updates)
```http
WS     /ws/notifications/                     # Real-time notification stream
```

**Flutter Service**: `lib/core/services/websocket_service.dart`

#### Health Checks (DevOps)
```http
GET /health/                  # Basic health check
GET /health/ready/            # Readiness probe (DB + Redis)
GET /health/live/             # Liveness probe
```

---

## 🐳 Docker Setup

### Development Environment

**Start all services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Stop services:**
```bash
docker-compose down
```

### Production Environment

**Start production stack:**
```bash
docker-compose -f docker-compose.production.yml --env-file .env.production up -d
```

**Scale services:**
```bash
# Scale public API to 5 instances
docker-compose -f docker-compose.production.yml up -d --scale django-public=5
```

**Full documentation**: [README.docker.md](README.docker.md)

---

## 🔄 CI/CD Pipelines

We provide **TWO** CI/CD solutions to demonstrate DevOps versatility:

### 🔹 Option 1: GitHub Actions (Recommended)

**Advantages**: Zero infrastructure, free, GitHub-native

**Setup**:
1. Add secrets to GitHub repository:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`
   - `EC2_HOST`
   - `EC2_USER`
   - `EC2_SSH_KEY`

2. Push to `master` branch triggers auto-deployment

**Pipeline Stages**:
- ✅ Run tests with MySQL + Redis services
- ✅ Build and push Docker image
- ✅ Deploy to EC2 via SSH
- ✅ Health check verification

**Configuration**: [.github/workflows/deploy.yml](.github/workflows/deploy.yml)

---

### 🔹 Option 2: Jenkins

**Advantages**: Enterprise-standard, self-hosted, extensive plugins

**Setup**:
1. Install Jenkins (see [docs/JENKINS_SETUP.md](docs/JENKINS_SETUP.md))
2. Configure credentials:
   - `dockerhub-cred` (Docker Hub token)
   - `ec2-key` (SSH private key)
3. Create pipeline job pointing to `Jenkinsfile`

**Pipeline Stages**:
- ✅ Checkout code
- ✅ Run Django tests
- ✅ Build Docker image
- ✅ Push to Docker Hub (prod only)
- ✅ Deploy to EC2 via SSH
- ✅ Health check
- ✅ Cleanup old images

**Configuration**: [Jenkinsfile](Jenkinsfile)

---

**Comparison**: [docs/CICD_COMPARISON.md](docs/CICD_COMPARISON.md)

---

## 🌍 Deployment

### AWS EC2 Deployment

**Server**: `YOUR-IP-SERVER`
**Domain**: `YOUR-DOMAIN`

#### Prerequisites
- EC2 instance (Ubuntu 22.04 LTS, t2.medium+)
- Docker installed on EC2
- Domain DNS configured

#### Step-by-Step Guide

1. **SSH to EC2:**
   ```bash
   ssh ubuntu@YOUR-IP-SERVER
   ```

2. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   ```

3. **Clone repository:**
   ```bash
   git clone https://github.com/momenawab/to7fabackend.git
   cd to7fabackend
   ```

4. **Create production environment file:**
   ```bash
   nano .env.production
   # Add production secrets (see Environment Variables section)
   ```

5. **Start production containers:**
   ```bash
   docker-compose -f docker-compose.production.yml --env-file .env.production up -d
   ```

6. **Run migrations:**
   ```bash
   docker-compose -f docker-compose.production.yml exec django-admin python manage.py migrate
   ```

7. **Verify deployment:**
   ```bash
   curl http://ip/health/
   ```

**Full guide**: [DEPLOY_EC2.md](DEPLOY_EC2.md)

---

## 🔐 Environment Variables

### Required Variables

```bash
# Core
ENVIRONMENT=production              # dev, staging, or production
DEBUG=False                         # Never True in production
SECRET_KEY=your-secret-key-here     # Generate with Django

# Domain & Security
ALLOWED_HOSTS=
CSRF_TRUSTED_ORIGINS=

# Database
DB_HOST=mysql                       # Service name in Docker
DB_NAME=to7fa_db
DB_USER=to7fa_user
DB_PASSWORD=strong-password-here
DB_PORT=3306

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Firebase (Push Notifications)
FCM_PROJECT_ID=your-firebase-project-id

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Templates
- Development: `.env.example`
- Production: `.env.production.example`

**⚠️ Never commit `.env` or `.env.production` files!**

---

## 📊 Monitoring & Health Checks

### Health Endpoints

```bash
# Basic health (always returns 200 OK)
curl http://YOUR-DOMAIN/health/

# Readiness check (verifies DB + Redis)
curl http://YOUR-DOMAIN/health/ready/

# Liveness check (app is running)
curl http://YOUR-DOMAIN/health/live/
```

### Docker Health Checks

Containers automatically restart if health checks fail:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=5)"
```

---

## 💼 About This Project

This is a **professional portfolio project** built to demonstrate full-stack development and DevOps expertise for job applications and technical interviews.

**Project Status**: Production-ready, actively maintained
**Purpose**: Portfolio showcase / Job application demonstration
**Visibility**: Public for recruiters and hiring managers to review

### Skills Demonstrated

This project showcases expertise in:
- ✅ **Backend Development**: Django, DRF, REST APIs
- ✅ **Mobile Development**: Flutter integration, token auth, WebSockets
- ✅ **Database Design**: MySQL, Redis caching
- ✅ **DevOps**: Docker, CI/CD (Jenkins + GitHub Actions), Nginx
- ✅ **Cloud Deployment**: AWS EC2, domain configuration
- ✅ **Security**: Environment-based secrets, HTTPS, CORS
- ✅ **Real-time Features**: Django Channels, WebSocket
- ✅ **Third-party Integration**: Firebase, payment gateways
- ✅ **Architecture**: Microservices, load balancing, scalability

---

## 📄 License

This project is **proprietary** and maintained by Momen Awab for professional demonstration purposes. The code is publicly viewable for portfolio review but not licensed for reuse or distribution.

**© 2024 Momen Awab. All Rights Reserved.**

---

## 👨‍💻 Author

**Momen Awab**

- GitHub: [@momenawab](https://github.com/momenawab)
- LinkedIn: [https://www.linkedin.com/in/momen-awab/]
- Email: [momenawab@gmail.com]

---

## 🙏 Acknowledgments

- Django & Django REST Framework teams
- Docker community
- Jenkins & GitHub Actions
- All open-source contributors

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by [Momen Awab](https://github.com/momenawab)

</div>
