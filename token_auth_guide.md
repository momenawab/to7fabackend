# Token Authentication in To7fa Backend

This guide explains how token authentication works in the To7fa backend API.

## Overview

The To7fa backend uses Django Rest Framework's Token Authentication, which is a simple token-based HTTP Authentication scheme. This authentication method is:

- Stateless (no server-side sessions)
- Suitable for client-server setups like mobile apps and SPAs
- Secure when used over HTTPS

## How It Works

1. **User Registration**: A new user registers with their email, password, and other required information
2. **User Login**: The user provides their credentials (email/username and password)
3. **Token Generation**: The server validates the credentials and generates a unique token
4. **Token Storage**: The token is stored in the database and returned to the client
5. **Authenticated Requests**: The client includes the token in the Authorization header for subsequent requests
6. **Token Validation**: The server validates the token before processing the request
7. **Logout**: The token is deleted from the database when the user logs out

## Implementation Details

### Backend Components

- **Token Model**: Uses Django Rest Framework's `Token` model from `rest_framework.authtoken`
- **Authentication Class**: Uses `TokenAuthentication` from DRF
- **Login View**: Custom `LoginView` extending `ObtainAuthToken` to return user details along with the token
- **Logout View**: Custom view to delete the user's token

### API Endpoints

- **Login**: `POST /api/auth/login/`
  - Request body: `{"username": "user@example.com", "password": "password123"}`
  - Response: `{"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b", "user_id": 1, ...}`

- **Logout**: `POST /api/auth/logout/`
  - Headers: `Authorization: Token <token>`
  - Response: `{"message": "Successfully logged out."}`

### Making Authenticated Requests

To make authenticated requests, include the token in the Authorization header:

```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## Security Considerations

- Always use HTTPS in production to prevent token interception
- Tokens do not expire automatically - implement token refresh or rotation for long-lived applications
- Consider implementing rate limiting to prevent brute force attacks
- Store tokens securely on the client side (secure storage for mobile apps, HttpOnly cookies for web apps)

## User Types and Permissions

The To7fa backend supports different user types with varying permissions:

1. **Customer**: Default user type with basic permissions
2. **Artist**: Seller type with permissions to manage their artworks
3. **Store**: Seller type with permissions to manage store products

Permissions are enforced through Django Rest Framework's permission classes and custom permission checks in the views.

## Seller Application Process

All users initially register as customers. To become a seller (artist or store), the following process is followed:

1. **Submit Application**: The authenticated customer submits a seller application:
   ```
   POST /api/auth/seller/apply/
   Header: Authorization: Token <token>
   ```
   With a detailed request body including:
   - Name
   - Photo (base64 encoded)
   - Contact information
   - Shipping details and costs
   - Categories
   - Additional details specific to artist or store

2. **Application Status**: The user can check their application status:
   ```
   GET /api/auth/seller/application/status/
   Header: Authorization: Token <token>
   ```

3. **Admin Approval**: An admin reviews and approves/rejects the application:
   ```
   POST /api/admin/seller-applications/{id}/approve/
   Header: Authorization: Token <admin_token>
   ```

4. **Seller Privileges**: Once approved, the user gains seller privileges and can access seller-specific endpoints.

## Example Authentication Flow

1. **Register a new user**:
   ```
   POST /api/auth/register/
   {
     "email": "user@example.com",
     "password": "securepassword123",
     "confirm_password": "securepassword123",
     "first_name": "John",
     "last_name": "Doe"
   }
   ```

2. **Login to get a token**:
   ```
   POST /api/auth/login/
   {
     "username": "user@example.com",
     "password": "securepassword123"
   }
   ```

3. **Response with token**:
   ```
   {
     "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
     "user_id": 1,
     "email": "user@example.com",
     "user_type": "customer",
     "first_name": "John",
     "last_name": "Doe"
   }
   ```

4. **Apply to become a seller**:
   ```
   POST /api/auth/seller/apply/
   Header: Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
   {
     "user_type": "store",
     "name": "Handcraft Treasures Store",
     "photo": "base64_encoded_image_data",
     "phone_number": "+1987654321",
     "email": "store@example.com",
     "address": "789 Store St, City, Country",
     "shipping_company": "Fast Delivery Co.",
     "shipping_costs": {
       "Cairo": 40,
       "Alexandria": 65,
       "Giza": 50,
       "Luxor": 90
     },
     "details": "We sell handcrafted items from local artisans.",
     "categories": [2, 4, 6],
     "store_name": "Handcraft Treasures",
     "tax_id": "TAX123456",
     "has_physical_store": true,
     "physical_address": "789 Store St, City, Country"
   }
   ```

5. **Make authenticated requests**:
   ```
   GET /api/auth/profile/
   Header: Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
   ```

6. **Logout to invalidate token**:
   ```
   POST /api/auth/logout/
   Header: Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
   ``` 