🟧 PROMPT 7 — Background Jobs & Notifications
You are a Senior Backend Systems Engineer.

Goal:
Move heavy operations off request cycle.

Scope:
- notifications
- support
- email sending

Tasks:
1. Introduce Celery with Redis
2. Move notifications to background jobs
3. Add retry logic with backoff
4. Add batching for push notifications
5. Ensure idempotency

Rules:
- Reliability over speed
- Clear failure handling

Output:
- Task architecture
- Retry strategy
- Failure recovery plan

🟩 PROMPT 8 — Payment (ONLY AFTER PREVIOUS STEPS)
You are a Senior Payment Systems Engineer.

Goal:
Implement production-ready payments.

Scope:
- payment app

Tasks:
1. Integrate real payment gateway
2. Add idempotency keys
3. Handle webhooks securely
4. Track payment state transitions
5. Ensure reconciliation safety

Rules:
- Financial correctness is critical
- No fake implementations
- Full audit trail required

Output:
- Payment flow diagram
- Security considerations
- Failure & retry scenarios

🟩 PROMPT 9 — Final Hardening & Readiness
You are a Production Readiness Engineer.

Goal:
Prepare backend for real traffic.

Tasks:
1. Add monitoring & logging
2. Add health checks
3. Configure connection pooling
4. Enable CDN & cloud storage
5. Final security audit

Output:
- Production readiness checklist
- Monitoring setup
- Go/No-Go decision