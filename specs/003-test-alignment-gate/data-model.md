# Data Model: Test Metadata & Gate Criteria

**Feature**: Spec 002 Test Alignment & Gate Stabilization
**Date**: 2026-02-07
**Purpose**: Define data structures for test classification, alignment rules, and gate criteria

## Overview

This document defines the data model for tracking test classification, alignment status, and gate determination. These are **metadata models** for test organization, not production data models.

## Entity: TestCase

**Purpose**: Represents a single test method with classification and status

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test_id` | string | Yes | Unique identifier: `filename.test_method_name` |
| `test_name` | string | Yes | Human-readable test name |
| `test_file` | string | Yes | File containing the test: `test_spec002_lifecycle.py` |
| `category` | enum | Yes | Test category: `lifecycle`, `cancellation`, `order_creation`, `payment`, `idempotency`, `inventory` |
| `classification` | enum | Yes | `critical`, `non_critical`, `deferred` |
| `classification_rationale` | string | Yes | Why this test has this classification |
| `alignment_status` | enum | Yes | `aligned`, `needs_alignment`, `deferred` |
| `current_status` | enum | Yes | `passing`, `failing`, `skipped` |
| `failure_reason` | string | No | If failing, why (e.g., "403 instead of 201", "Model name mismatch") |
| `alignment_action` | string | No | For needs_alignment: what change is needed |

### Enums

```python
class TestCategory(Enum):
    LIFECYCLE = "lifecycle"
    CANCELLATION = "cancellation"
    ORDER_CREATION = "order_creation"
    PAYMENT = "payment"
    IDEMPOTENCY = "idempotency"
    INVENTORY = "inventory"

class TestClassification(Enum):
    CRITICAL = "critical"  # Gate-blocking: business logic validation
    NON_CRITICAL = "non_critical"  # Non-blocking: API contract, implementation details
    DEFERRED = "deferred"  # Out of scope: infrastructure dependencies

class AlignmentStatus(Enum):
    ALIGNED = "aligned"  # Test matches production implementation
    NEEDS_ALIGNMENT = "needs_alignment"  # Test needs changes to match production
    DEFERRED = "deferred"  # Test deferred due to infrastructure or scope

class TestStatus(Enum):
    PASSING = "passing"
    FAILING = "failing"
    SKIPPED = "skipped"
```

## Entity: TestClassification

**Purpose**: Defines classification criteria and rules

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `classification_type` | enum | Yes | `critical`, `non_critical`, `deferred` |
| `criteria` | string | Yes | Description of what makes a test fit this classification |
| `examples` | list[string] | Yes | Example test patterns that match |
| `gate_blocking` | boolean | Yes | Whether this classification blocks the gate |

### Classification Criteria

```yaml
critical:
  criteria: "Validates core business logic invariants"
  examples:
    - "State machine transitions (OrderStateMachine)"
    - "Atomicity guarantees (transaction rollback)"
    - "Idempotency enforcement (duplicate prevention)"
    - "Multi-seller aggregation logic"
  gate_blocking: true

non_critical:
  criteria: "Validates API contract or implementation details"
  examples:
    - "HTTP method usage (POST vs PUT)"
    - "HTTP status codes (403 vs 405 vs 200)"
    - "Model naming conventions (Transaction vs WalletTransaction)"
    - "Internal function signatures"
  gate_blocking: false

deferred:
  criteria: "Requires unavailable infrastructure or production changes"
  examples:
    - "Redis dependency"
    - "Celery runtime dependency"
    - "Payment provider integration"
    - "Tests requiring model refactoring"
  gate_blocking: false
```

## Entity: AlignmentRule

**Purpose**: Maps test expectations to production implementation reality

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rule_id` | string | Yes | Unique identifier for the rule |
| `rule_name` | string | Yes | Human-readable name |
| `test_expectation` | string | Yes | What tests currently expect |
| `production_reality` | string | Yes | What production actually does |
| `alignment_action` | string | Yes | How to align the test |
| `affected_tests` | list[string] | Yes | List of test_ids affected by this rule |
| `priority` | enum | Yes | `high`, `medium`, `low` |

### Alignment Rules Catalog

```yaml
rule_001:
  rule_name: "Cancellation HTTP Method"
  test_expectation: "POST /orders/{id}/cancel/"
  production_reality: "PUT /orders/{id}/cancel/"
  alignment_action: "Change test client to use PUT method"
  affected_tests:
    - "test_spec002_cancellation.py::test_customer_can_cancel_pending_order"
    - "test_spec002_cancellation.py::test_customer_can_cancel_paid_order"
    # ... all cancellation tests
  priority: "high"

rule_002:
  rule_name: "Cart Item Creation"
  test_expectation: "cart.items = [{product, quantity}]"
  production_reality: "cart.add_item(product=product, quantity=quantity)"
  alignment_action: "Use Cart.add_item() method instead of direct assignment"
  affected_tests:
    - "test_spec002_order_creation.py::test_order_creation_with_cart_items"
    # ... cart-related tests
  priority: "high"

rule_003:
  rule_name: "Wallet Transaction Model"
  test_expectation: "WalletTransaction.objects.create(...)"
  production_reality: "Transaction.objects.create(...)"
  alignment_action: "Use Transaction model (may alias as WalletTransaction in tests)"
  affected_tests:
    - "test_spec002_payment.py::test_reserve_payment"
    - "test_spec002_payment.py::test_capture_payment"
    # ... wallet tests
  priority: "medium"

rule_004:
  rule_name: "Cancellation Status Codes"
  test_expectation: "403 Forbidden for shipped order cancellation"
  production_reality: "200 OK (implementation allows cancellation)"
  alignment_action: "Accept 200, 201, or 403 OR defer as implementation choice"
  affected_tests:
    - "test_spec002_cancellation.py::test_customer_cannot_cancel_shipped_order"
  priority: "low"
```

## Entity: GateCriteria

**Purpose**: Defines conditions for Spec 002 to be marked STABLE

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `criterion_id` | string | Yes | Unique identifier |
| `criterion_name` | string | Yes | Human-readable name |
| `condition` | string | Yes | Pass/fail condition |
| `threshold` | string/number | Yes | Required threshold (e.g., "100%", "35/35") |
| `measurement_method` | string | Yes | How to measure this criterion |
| `blocking` | boolean | Yes | Whether failure blocks the gate |

### Gate Criteria Definition

```yaml
gc_001:
  criterion_name: "Lifecycle Tests Pass"
  condition: "All OrderStateMachine lifecycle tests pass"
  threshold: "35/35 tests (100%)"
  measurement_method: "Run pytest orders/tests/test_spec002_lifecycle.py"
  blocking: true

gc_002:
  criterion_name: "Idempotency Tests Pass"
  condition: "Core business invariant tests pass"
  threshold: "10/13 tests (77%+)"
  measurement_method: "Run pytest orders/tests/test_spec002_idempotency.py"
  blocking: true

gc_003:
  criterion_name: "Critical Tests Classified"
  condition: "All critical tests identified and documented"
  threshold: "50-60 tests with rationale"
  measurement_method: "Review test-classification.md"
  blocking: true

gc_004:
  criterion_name: "No Business Rule Violations"
  condition: "No failing critical test indicates business logic bug"
  threshold: "0 violations"
  measurement_method: "Review failing critical tests"
  blocking: true

gc_005:
  criterion_name: "Non-Critical Failures Documented"
  condition: "All non-critical failures documented as deferred debt"
  threshold: "100% of non-critical failures"
  measurement_method: "Review deferred-test-debt.md"
  blocking: false

gc_006:
  criterion_name: "Gate Verdict Produced"
  condition: "Gate verdict document exists with clear decision"
  threshold: "PASS/CONDITIONAL_PASS/FAIL with justification"
  measurement_method: "Review gate-verdict.md"
  blocking: true
```

## Entity: GateVerdict

**Purpose**: Final gate decision with justification

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verdict` | enum | Yes | `PASS`, `CONDITIONAL_PASS`, `FAIL` |
| `decision_date` | date | Yes | When the gate decision was made |
| `critical_tests_passing` | number | Yes | Count of passing critical tests |
| `critical_tests_total` | number | Yes | Total count of critical tests |
| `blocking_violations` | list[string] | No | List of gate-blocking violations |
| `deferred_debt_count` | number | Yes | Count of deferred tests |
| `justification` | string | Yes | Detailed explanation of the decision |
| `recommendations` | list[string] | No | Recommended next steps |

### Verdict Enum

```python
class GateVerdict(Enum):
    PASS = "PASS"  # All critical tests pass, no violations
    CONDITIONAL_PASS = "CONDITIONAL_PASS"  # Core logic passes, some non-critical failures documented
    FAIL = "FAIL"  # Critical tests fail or business rule violations exist
```

## Relationships

```
TestCase (1) --> TestClassification (many)
TestCase (1) --> AlignmentRule (many)
TestCase (many) --> GateCriteria (many)
GateCriteria (many) --> GateVerdict (1)
```

## Validation Rules

1. **All tests must have a classification** (critical, non_critical, or deferred)
2. **Critical tests must align or be justified** (cannot be "needs_alignment" without rationale)
3. **Deferred tests must have a reason** (infrastructure, scope, or future_work)
4. **Gate verdict requires all blocking criteria to be evaluated**
5. **Conditional pass requires no critical test failures**

## Usage Example

```python
# Classify a test
lifecycle_test = TestCase(
    test_id="test_spec002_lifecycle.py::test_valid_state_transition_pending_to_paid",
    test_name="test_valid_state_transition_pending_to_paid",
    test_file="test_spec002_lifecycle.py",
    category=TestCategory.LIFECYCLE,
    classification=TestClassification.CRITICAL,
    classification_rationale="Validates OrderStateMachine state transition",
    alignment_status=AlignmentStatus.ALIGNED,
    current_status=TestStatus.PASSING
)

# Apply alignment rule
cancellation_test = TestCase(
    test_id="test_spec002_cancellation.py::test_customer_can_cancel_paid_order",
    classification=TestClassification.NON_CRITICAL,
    alignment_status=AlignmentStatus.NEEDS_ALIGNMENT,
    alignment_action="Change POST to PUT per rule_001"
)

# Generate gate verdict
verdict = GateVerdict(
    verdict=GateVerdict.CONDITIONAL_PASS,
    critical_tests_passing=45,
    critical_tests_total=50,
    deferred_debt_count=30,
    justification="All critical business logic tests pass. Non-critical API contract differences documented as deferred debt."
)
```

## Metadata Persistence

**Note**: These entities are for test organization and gate determination. They are **not** stored in the database. Instead, they are represented as:

1. **Markdown documentation** (test-classification.md, alignment-rules.md)
2. **JSON artifacts** (gate-verdict.json for automated gate checking)
3. **Test metadata decorators** (pytest marks for classification)

```python
# Example: pytest marks for classification
@pytest.mark.critical
@pytest.mark.classification("business_logic")
def test_order_state_transition():
    ...

@pytest.mark.non_critical
@pytest.mark.alignment_needed("rule_001")
def test_cancel_order_http_method():
    ...

@pytest.mark.deferred
@pytest.mark.reason("infrastructure: Redis not available")
def test_cache_invalidation():
    ...
```
