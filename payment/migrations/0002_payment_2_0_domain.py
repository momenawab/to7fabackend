"""
Phase 3 (Payment 2.0, Part B): replaces the fake-success `Payment` model with the real
domain (Payment / PaymentAttempt / GatewayTransaction / Refund / WebhookEvent).

PRODUCTION SAFETY NOTE (same pattern as orders/migrations/0010's docstring): this
migration DELETES and recreates the `payment_payment` table rather than altering it in
place. That is only safe because nothing has ever written a row to it. Verified before
writing this migration, not assumed:
  - payment/views.py's process_payment() (the fake-success stub being replaced this
    phase) never called Payment.objects.create() anywhere - it just returned a
    hardcoded Response.
  - `grep -rn "payment\\.models\\|Payment\\.objects\\|PaymentMethod\\.objects"` across
    the entire repo (excluding payment/models.py and payment/views.py themselves)
    turns up only payment/admin.py's registration - no other app reads or writes
    these models.
Before this migration is ever applied to a database this wasn't verified against
(e.g. a separately-seeded production database), re-run:
    python manage.py dbshell -c "SELECT COUNT(*) FROM payment_payment;"
and confirm it is 0. If it is not 0, STOP - this migration will destroy that data, and
this migration must be redesigned as a proper column-preserving migration instead.
`PaymentMethod` is untouched by this migration - it is unaffected by the fake-success
bug and had no schema change.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0010_add_missing_orderitem_indexes'),
        ('payment', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(name='Payment'),

        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gateway', models.CharField(default='paymob', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='EGP', max_length=3)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending'), ('processing', 'Processing'), ('paid', 'Paid'),
                    ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded'),
                    ('partially_refunded', 'Partially Refunded'),
                ], default='pending', max_length=20)),
                ('amount_refunded', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('idempotency_key', models.CharField(default='', max_length=255, unique=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='gateway_payment', to='orders.order')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='gateway_payments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user', '-created_at'], name='payment_pay_user_id_2df5ec_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status'], name='payment_pay_status_124d3d_idx'),
        ),

        migrations.CreateModel(
            name='PaymentAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending'), ('processing', 'Processing'),
                    ('succeeded', 'Succeeded'), ('failed', 'Failed'),
                ], default='pending', max_length=20)),
                ('gateway_reference', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('failure_reason', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='payment.payment')),
            ],
            options={'ordering': ['-created_at']},
        ),

        migrations.CreateModel(
            name='GatewayTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gateway_transaction_id', models.CharField(db_index=True, max_length=255)),
                ('is_success', models.BooleanField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('raw_response', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='payment.paymentattempt')),
            ],
        ),
        migrations.AddConstraint(
            model_name='gatewaytransaction',
            constraint=models.UniqueConstraint(fields=('gateway_transaction_id',), name='payment_gatewaytransaction_unique_gateway_txn_id'),
        ),

        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reason', models.TextField(blank=True)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending'), ('processing', 'Processing'),
                    ('succeeded', 'Succeeded'), ('failed', 'Failed'),
                ], default='pending', max_length=20)),
                ('gateway_refund_id', models.CharField(blank=True, max_length=255, null=True)),
                ('idempotency_key', models.CharField(default='', max_length=255, unique=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refunds', to='payment.payment')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='requested_refunds', to=settings.AUTH_USER_MODEL)),
            ],
        ),

        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gateway', models.CharField(max_length=20)),
                ('event_id', models.CharField(blank=True, max_length=255, null=True)),
                ('signature_valid', models.BooleanField()),
                ('processed', models.BooleanField(default=False)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name='webhookevent',
            constraint=models.UniqueConstraint(fields=('gateway', 'event_id'), name='payment_webhookevent_unique_gateway_event'),
        ),
    ]
