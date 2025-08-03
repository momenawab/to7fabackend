# تحفة (Tohfa) Backend

This is the backend API for the Tohfa artisanal marketplace Flutter application.

## Features

- User authentication with JWT
- User types: Customer, Artist, Store
- Product management
- Order processing
- Wallet and transactions
- Payment processing
- Notifications

## Technology Stack

- Django 5.2
- Django REST Framework
- MySQL
- JWT Authentication

## Prerequisites

- Python 3.10+
- MySQL Server
- pip

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd to7fa_backend
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up MySQL

Make sure MySQL server is running, then:

```bash
# Option 1: Run the setup script
python setup_mysql.py

# Option 2: Manual setup
# Create database
mysql -u root -e "CREATE DATABASE IF NOT EXISTS to7fa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 5. Run the development server

```bash
python manage.py runserver
```

The API will be available at http://127.0.0.1:8000/

## API Endpoints

### Authentication

```
POST /api/auth/token/            # Get JWT token
POST /api/auth/token/refresh/    # Refresh JWT token
POST /api/auth/register/         # Register new user
```

### User Management

```
GET /api/auth/profile/           # Get user profile
PUT /api/auth/profile/           # Update user profile
POST /api/auth/seller/apply/     # Apply to become a seller (artist/store)
GET /api/auth/seller/application/status/  # Check application status
```

### Admin

```
GET /api/admin/seller-applications/       # List all seller applications (admin only)
POST /api/admin/seller-applications/{id}/approve/  # Approve/reject seller application
```

### Products

```
GET /api/products/               # List products
POST /api/products/              # Create product (sellers only)
GET /api/products/{id}/          # Get product details
PUT /api/products/{id}/          # Update product (seller only)
DELETE /api/products/{id}/       # Delete product (seller only)
```

### Orders

```
GET /api/orders/                 # List user orders
POST /api/orders/create/         # Create order
GET /api/orders/{id}/            # Get order details
PUT /api/orders/{id}/cancel/     # Cancel order
```

### Wallet

```
GET /api/wallet/                 # Get wallet details
POST /api/wallet/deposit/        # Deposit funds
POST /api/wallet/withdraw/       # Withdraw funds
GET /api/wallet/transactions/    # Get transaction history
```

## User Types

The system has three user types:

1. **Customer**
   - Can browse and purchase products
   - Has a wallet for payments
   - Can leave reviews

2. **Artist**
   - Can sell handmade products
   - Has a profile with specialty and bio
   - Can manage orders for their products
   - Must apply and be approved by admin

3. **Store**
   - Can sell multiple products
   - Has a store profile with details
   - Can manage orders for their products
   - Must apply and be approved by admin

## Seller Application Process

All users register initially as customers. To become a seller:

1. Submit a seller application with required details:
   - Name
   - Photo
   - Contact information
   - Shipping details
   - Categories
   - Additional details specific to artist or store

2. Admin reviews the application and approves or rejects

3. Once approved, the user gains seller privileges

## Project Structure

```
to7fabackend/
├── to7fabackend/          # Project settings
├── custom_auth/           # Authentication and user profiles
├── products/              # Product management
├── orders/                # Order processing
├── wallet/                # Wallet and transactions
├── payment/               # Payment processing
└── notifications/         # User notifications
```

## License

[MIT License](LICENSE)

# To7fa API Postman Collection

This repository contains a Postman collection for testing the To7fa backend API with token authentication.

## Setup Instructions

1. Install [Postman](https://www.postman.com/downloads/)
2. Import the collection file `to7fa_postman_collection.json`
3. Import the environment file `postman_environment.json`
4. Select the "To7fa API Environment" from the environment dropdown in Postman

## Authentication

The API uses token-based authentication. Here's how to authenticate:

1. Register a new user using the "Register User" request in the Authentication folder
2. Login using the "Login" request - this will automatically set the auth token in your environment
3. All authenticated requests will now use this token

## User Types

### Default User (Customer)
- Can browse products
- Can place orders
- Can leave reviews
- Can manage their profile

### Seller Application Process
- All users start as customers
- Can apply to become a seller (artist or store)
- Must provide detailed information including:
  - Name
  - Photo
  - Phone number
  - Email
  - Address
  - Shipping company
  - Shipping costs for each governorate
  - Categories
  - Additional details
- Admin must approve applications before seller status is granted

### Seller (Artist)
- All customer capabilities
- Can create and manage their own products
- Can view and update orders for their products

### Seller (Store)
- All customer capabilities
- Can create and manage their own products
- Can view and update orders for their products
- Has store-specific fields

## API Endpoints

### Authentication
- Register: `POST /api/auth/register/`
- Login: `POST /api/auth/login/`
- Logout: `POST /api/auth/logout/`
- Get Profile: `GET /api/auth/profile/`
- Update Profile: `PUT /api/auth/profile/`
- Apply as Seller: `POST /api/auth/seller/apply/`
- Check Application Status: `GET /api/auth/seller/application/status/`

### Admin
- List Seller Applications: `GET /api/admin/seller-applications/`
- Approve/Reject Application: `POST /api/admin/seller-applications/{id}/approve/`

### Products
- List Products: `GET /api/products/`
- Product Detail: `GET /api/products/{id}/`
- Search Products: `GET /api/products/search/?q={query}`
- List Categories: `GET /api/products/categories/`

### Seller Products
- List Seller Products: `GET /api/products/seller/`
- Create Product: `POST /api/products/seller/`
- Update Product: `PUT /api/products/seller/{id}/`
- Delete Product: `DELETE /api/products/seller/{id}/`

### Orders
- List Orders: `GET /api/orders/`
- Order Detail: `GET /api/orders/{id}/`
- Create Order: `POST /api/orders/create/`
- Cancel Order: `PUT /api/orders/{id}/cancel/`

### Seller Orders
- List Seller Orders: `GET /api/orders/seller/`
- Update Order Status: `PUT /api/orders/seller/{id}/status/`

### Wallet
- Wallet Details: `GET /api/wallet/`
- Deposit Funds: `POST /api/wallet/deposit/`
- Withdraw Funds: `POST /api/wallet/withdraw/`
- Transaction History: `GET /api/wallet/transactions/`

### Notifications
- List Notifications: `GET /api/notifications/`
- Mark as Read: `PUT /api/notifications/{id}/read/`
- Mark All as Read: `PUT /api/notifications/read-all/`

## Token Authentication

For authenticated endpoints, include the token in the Authorization header:

```
Authorization: Token your_token_here
```

The Postman collection automatically sets this header when you use the Login request, which stores the token in the environment variables. 