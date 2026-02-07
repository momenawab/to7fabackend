# Running Tests

This document provides instructions for running the Django backend tests for user state logic implementation.

## Prerequisites

Before running tests, ensure you have:

1. Python 3.9+ installed
2. Django 4.2.13 installed
3. All dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

## Test Configuration

Tests use a custom settings file: [`test_settings.py`](../test_settings.py)

Key configuration:
- **Database**: SQLite in-memory (`:memory:`)
- **Password Hashing**: MD5 (for fast test execution)
- **Migrations**: Disabled
- **CSRF**: Disabled for API testing
- **Throttling**: Disabled for tests

## Running All Tests

Run all tests using Django's test runner:

```bash
python manage.py test --settings=to7fabackend.test_settings --verbosity=2
```

### Verbosity Levels

- `--verbosity=0` - Silent
- `--verbosity=1` - Normal (default)
- `--verbosity=2` - Verbose (shows individual test names)
- `--verbosity=3` - Very verbose (shows all output)

## Running Specific App Tests

### Run Custom Auth Tests

```bash
python manage.py test custom_auth --settings=to7fabackend.test_settings --verbosity=2
```

### Run Cart Tests

```bash
python manage.py test cart --settings=to7fabackend.test_settings --verbosity=2
```

## Running Specific Test Files

### Run User Model Tests

```bash
python manage.py test custom_auth.tests.test_user_model --settings=to7fabackend.test_settings --verbosity=2
```

### Run Login User State Tests

```bash
python manage.py test custom_auth.tests.test_user_state --settings=to7fabackend.test_settings --verbosity=2
```

### Run Lock Enforcement Tests

```bash
python manage.py test custom_auth.tests.test_lock_block --settings=to7fabackend.test_settings --verbosity=2
```

### Run OTP Verification Tests

```bash
python manage.py test custom_auth.tests.test_verification --settings=to7fabackend.test_settings --verbosity=2
```

### Run Cart Tests

```bash
python manage.py test cart.tests.test_cart --settings=to7fabackend.test_settings --verbosity=2
```

## Running Specific Test Classes

### Run User Model Extensions Tests

```bash
python manage.py test custom_auth.tests.test_user_model.TestUserModelExtensions --settings=to7fabackend.test_settings --verbosity=2
```

### Run Login User State Tests

```bash
python manage.py test custom_auth.tests.test_user_state.TestLoginUserState --settings=to7fabackend.test_settings --verbosity=2
```

### Run Lock Enforcement Tests

```bash
python manage.py test custom_auth.tests.test_lock_block.TestLockEnforcement --settings=to7fabackend.test_settings --verbosity=2
```

### Run OTP Send Tests

```bash
python manage.py test custom_auth.tests.test_verification.TestOTPSend --settings=to7fabackend.test_settings --verbosity=2
```

### Run OTP Verify Tests

```bash
python manage.py test custom_auth.tests.test_verification.TestOTPVerify --settings=to7fabackend.test_settings --verbosity=2
```

### Run Guest Cart Creation Tests

```bash
python manage.py test cart.tests.test_cart.TestGuestCartCreation --settings=to7fabackend.test_settings --verbosity=2
```

### Run Guest Cart Operations Tests

```bash
python manage.py test cart.tests.test_cart.TestGuestCartOperations --settings=to7fabackend.test_settings --verbosity=2
```

### Run Cart Merge Tests

```bash
python manage.py test cart.tests.test_cart.TestCartMerge --settings=to7fabackend.test_settings --verbosity=2
```

## Running Specific Test Methods

### Run Single Test Method

```bash
python manage.py test custom_auth.tests.test_user_model.TestUserModelExtensions.test_default_is_mobile_verified_is_false --settings=to7fabackend.test_settings --verbosity=2
```

## Using pytest

If you prefer pytest, you can also run tests using pytest-django:

```bash
pytest --ds=to7fabackend.test_settings -v
```

### Run Specific Test File with pytest

```bash
pytest custom_auth/tests/test_user_model.py --ds=to7fabackend.test_settings -v
```

### Run Specific Test Class with pytest

```bash
pytest custom_auth/tests/test_user_model.py::TestUserModelExtensions --ds=to7fabackend.test_settings -v
```

### Run Specific Test Method with pytest

```bash
pytest custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_is_mobile_verified_is_false --ds=to7fabackend.test_settings -v
```

## Test Output

### Successful Test Run

```
Found 71 test(s).

test_default_is_mobile_verified_is_false (custom_auth.tests.test_user_model.TestUserModelExtensions) ... ok
test_default_is_locked_is_false (custom_auth.tests.test_user_model.TestUserModelExtensions) ... ok
...
----------------------------------------------------------------------
Ran 71 tests in 2.345s

OK
```

### Failed Test Run

```
Found 71 test(s).

test_default_is_mobile_verified_is_false (custom_auth.tests.test_user_model.TestUserModelExtensions) ... FAIL
...
----------------------------------------------------------------------
Ran 71 tests in 2.345s

FAILED (failures=1)
```

## Test Coverage

To generate a coverage report:

```bash
coverage run --source='.' manage.py test --settings=to7fabackend.test_settings
coverage report
```

To generate HTML coverage report:

```bash
coverage html
```

Open `htmlcov/index.html` in your browser to view the report.

## Common Issues

### Import Error: No module named 'rest_framework'

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Database Error: no such table

**Solution**: Ensure you're using test settings:
```bash
python manage.py test --settings=to7fabackend.test_settings
```

### ModuleNotFoundError: No module named 'to7fabackend'

**Solution**: Ensure you're running from the project root directory:
```bash
cd /path/to/to7fabackend
python manage.py test --settings=to7fabackend.test_settings
```

### Tests Running Slowly

**Solution**: The test settings are already optimized for speed. If tests are still slow, ensure:
- You're using in-memory SQLite (configured in test_settings.py)
- Migrations are disabled (configured in test_settings.py)
- MD5 password hashing is enabled (configured in test_settings.py)

## Continuous Integration

For CI/CD pipelines, use:

```bash
python manage.py test --settings=to7fabackend.test_settings --verbosity=2 --failfast
```

The `--failfast` flag stops testing on the first failure, useful for quick feedback.

## Test Documentation

- **Test Summary**: See [`TEST_SUMMARY.md`](TEST_SUMMARY.md) for an overview of all tests
- **Coverage Report**: See [`COVERAGE_REPORT.md`](COVERAGE_REPORT.md) for detailed coverage information

## Best Practices

1. **Run tests before committing**: Always run tests before pushing code
2. **Use verbose mode**: Use `--verbosity=2` to see which tests are running
3. **Fix failures immediately**: Don't accumulate test failures
4. **Write tests for new features**: Maintain high test coverage
5. **Keep tests isolated**: Each test should be independent
6. **Use descriptive names**: Test method names should clearly describe what they test

## Test Statistics

| Category | Test Methods |
|-----------|--------------|
| User Model | 18 |
| Login User State | 11 |
| Lock Enforcement | 9 |
| OTP Verification | 12 |
| Cart | 21 |
| **Total** | **71** |

## Additional Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
