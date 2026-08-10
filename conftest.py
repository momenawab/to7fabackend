"""
Pytest configuration for Django project.

Phase 4 (Part 15, test infrastructure): this file used to define its own `db` fixture
(a hand-rolled `TestCase()._pre_setup()`/`_post_teardown()` wrapper) that shadowed
pytest-django's real, built-in `db` fixture of the same name. pytest-django's actual
database-access blocker is only lifted by its OWN db/transactional_db fixture
machinery; the hand-rolled replacement never called into that machinery, so any test
using plain `db` (directly or via the `@pytest.mark.django_db` marker, which is the
overwhelming majority of this suite) could fail with
`RuntimeError: Database access not allowed, use the "django_db" mark...` depending on
what had already run earlier in the same session and incidentally left the blocker
lifted. This was the root cause of ~150 of the ~230 non-passing tests recorded at the
end of Phase 3 (PHASE3_API_PAYMENT_REPORT.md's baseline). The custom fixture is
removed entirely below; pytest-django's own `db` fixture (provided by the
pytest-django plugin, needs no import or registration here) is used instead, and every
fixture in this file that took `db` as a dependency is unaffected - the fixture name is
unchanged, only which implementation answers it. See
PHASE4_PRODUCTION_READINESS_REPORT.md for the full investigation and before/after
numbers.
"""
import os
import pytest
from decimal import Decimal

# Set Django settings module BEFORE any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')

# Set ALLOWED_HOSTS environment variable for tests
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')

import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "django_db: mark test to use the database"
    )
    config.addinivalue_line(
        "markers", "skip_otp: skip tests that require OTP/SMS services"
    )
    config.addinivalue_line(
        "markers", "skip_redis: skip tests that require Redis"
    )
    config.addinivalue_line(
        "markers", "critical: mark test as critical (gate-blocking business logic)"
    )
    config.addinivalue_line(
        "markers", "non_critical: mark test as non-critical (API contract, implementation details)"
    )
    config.addinivalue_line(
        "markers", "deferred: mark test as deferred (infrastructure dependencies, future work)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip tests that require external services or
    that don't work with the current auth setup.
    """
    skip_otp = pytest.mark.skip(reason="OTP tests require SMS integration")
    skip_redis = pytest.mark.skip(reason="Tests require Redis connection")
    skip_middleware = pytest.mark.skip(
        reason="Middleware tests don't work with JWT auth (auth happens at view level)"
    )
    
    for item in items:
        # Skip all tests in test_verification.py
        if "test_verification" in str(item.fspath):
            item.add_marker(skip_otp)
        
        # Skip login tests that use Redis for rate limiting
        if "TestLockEnforcement" in item.nodeid and "login" not in item.name.lower():
            # These non-login tests need Redis
            if "redis" in item.name.lower() or "rate" in item.name.lower():
                item.add_marker(skip_redis)
        
        # Skip all TestLockEnforcement tests (they use Redis for login rate limiting)
        if "TestLockEnforcement::" in item.nodeid and "Middleware" not in item.nodeid:
            item.add_marker(skip_redis)
        
        # Skip middleware tests (JWT auth happens at view level, not middleware)
        if "TestLockEnforcementMiddleware" in item.nodeid:
            item.add_marker(skip_middleware)
        
        # Skip cart merge via login test (requires Redis)
        if "test_merge_via_login_endpoint" in item.name:
            item.add_marker(skip_redis)




@pytest.fixture
def user(db):
    """Create a test user with unique email."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return User.objects.create_user(
        email=f'testuser_{unique_id}@example.com',
        password='testpass123',
        user_type='customer'
    )


@pytest.fixture
def api_client():
    """Return an API client for testing."""
    from rest_framework.test import APIClient
    client = APIClient()
    # Set HTTP_HOST to 'testserver' which is in ALLOWED_HOSTS
    client.defaults['HTTP_HOST'] = 'testserver'
    return client


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    from rest_framework_simplejwt.tokens import RefreshToken
    
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return api_client


@pytest.fixture
def product(user, db):
    """Create a test product for order tests.

    Phase 4: approval_status='approved' added - Phase 2's visibility enforcement
    (Product.objects.approved()) correctly rejects orders containing unapproved
    products, and this fixture's products were pending by default, so every order
    test using it failed with ProductVisibilityError once the `db` fixture bug
    (above) stopped masking it.
    """
    from products.models import Product, Category
    import uuid
    
    # Create a seller user for product
    seller = User.objects.create_user(
        email=f'seller_{str(uuid.uuid4())[:8]}@example.com',
        password='testpass123',
        user_type='artist'
    )
    
    # Create a category for product
    category = Category.objects.create(
        name=f'Test Category {str(uuid.uuid4())[:8]}',
        description='A test category for order tests'
    )
    
    # Create a product
    product = Product.objects.create(
        seller=seller,
        name=f'Test Product {str(uuid.uuid4())[:8]}',
        description='A test product for order tests',
        base_price=Decimal('100.00'),
        stock_quantity=50,
        category=category,
        is_active=True,
        approval_status='approved'
    )
    
    return product


@pytest.fixture
def product_with_stock(db):
    """Create a test product with stock for order tests. See `product` above for why
    approval_status='approved' is required here too.

    Phase 4 (Part 15, test infrastructure): also fixes the same missing-Category-
    import NameError as another_product below - each of these three fixtures does its
    own local import rather than sharing one at module scope, and this one had the
    same gap.
    """
    from products.models import Product, Category
    from django.contrib.auth import get_user_model
    import uuid
    
    User = get_user_model()
    
    # Create a seller user for product
    seller = User.objects.create_user(
        email=f'seller_stock_{str(uuid.uuid4())[:8]}@example.com',
        password='testpass123',
        user_type='artist'
    )
    
    # Create a category for product
    category = Category.objects.create(
        name=f'Test Category Stock {str(uuid.uuid4())[:8]}',
        description='A test category for order tests'
    )
    
    # Create a product with stock
    product = Product.objects.create(
        seller=seller,
        name=f'Test Product Stock {str(uuid.uuid4())[:8]}',
        description='A test product with stock',
        base_price=Decimal('50.00'),
        stock_quantity=100,
        category=category,
        is_active=True,
        approval_status='approved'
    )
    
    return product


@pytest.fixture
def another_product(db):
    """Create another test product for multi-item tests. See `product` above for why
    approval_status='approved' is required here too.

    Phase 4 (Part 15, test infrastructure): also fixes `NameError: name 'Category' is
    not defined` - Category was used below without ever being imported in this
    fixture (product/product_with_stock import it from products.models; this one
    never did). Masked until now by the conftest.py `db` fixture bug.
    """
    from products.models import Product, Category
    from django.contrib.auth import get_user_model
    import uuid
    
    User = get_user_model()
    
    # Create a seller user for product
    seller = User.objects.create_user(
        email=f'seller_another_{str(uuid.uuid4())[:8]}@example.com',
        password='testpass123',
        user_type='artist'
    )
    
    # Create a category for product
    category = Category.objects.create(
        name=f'Test Category Another {str(uuid.uuid4())[:8]}',
        description='Another test category'
    )
    
    # Create a product
    product = Product.objects.create(
        seller=seller,
        name=f'Another Product {str(uuid.uuid4())[:8]}',
        description='Another test product',
        base_price=Decimal('75.00'),
        stock_quantity=200,
        category=category,
        is_active=True,
        approval_status='approved'
    )
    
    return product


@pytest.fixture
def user_wallet(user, db):
    """Create a wallet for test user."""
    from wallet.models import Wallet
    
    # Check if wallet already exists for this user
    wallet, created = Wallet.objects.get_or_create(
        user=user,
        defaults={'balance': Decimal('1000.00')}
    )
    
    return wallet
