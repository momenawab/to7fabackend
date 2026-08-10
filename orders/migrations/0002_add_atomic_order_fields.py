# Generated migration for atomic order system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='idempotency_key',
            field=models.CharField(
                max_length=255,
                unique=True,
                null=True,
                blank=True,
                db_index=True,
                help_text="Unique key to prevent duplicate orders from retries"
            ),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='variant_id',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text="ID of product variant ordered"
            ),
        ),
        migrations.AlterModelOptions(
            name='order',
            options={
                'indexes': [
                    models.Index(fields=['user', '-created_at'], name='orders_order_user_created_at_idx'),
                    models.Index(fields=['status'], name='orders_order_status_idx'),
                    models.Index(fields=['idempotency_key'], name='orders_order_idempotency_key_idx'),
                ]
            },
        ),
        migrations.AlterModelOptions(
            name='orderitem',
            options={
                'indexes': [
                    models.Index(fields=['order', 'product'], name='orderitem_order_product_idx'),
                    models.Index(fields=['seller'], name='orderitem_seller_idx'),
                    models.Index(fields=['variant_id'], name='orderitem_variant_id_idx'),
                ]
            },
        ),
    ]
