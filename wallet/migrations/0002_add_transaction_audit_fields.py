# Generated migration for wallet concurrency safety improvements

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0001_initial'),
        ('custom_auth', '0001_initial'),  # For User foreign key
    ]

    operations = [
        # Add audit fields to Transaction model
        migrations.AddField(
            model_name='transaction',
            name='balance_before',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='balance_after',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='idempotency_key',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='performed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='performed_transactions',
                to='custom_auth.user'
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='user_agent',
            field=models.TextField(blank=True, null=True),
        ),
        
        # Create BalanceSnapshot model
        migrations.CreateModel(
            name='BalanceSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, max_digits=10)),
                ('snapshot_date', models.DateTimeField(auto_now_add=True)),
                ('transaction_count', models.IntegerField(default=0)),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='balance_snapshots', to='wallet.wallet')),
            ],
            options={
                'verbose_name': 'Balance Snapshot',
                'verbose_name_plural': 'Balance Snapshots',
                'ordering': ['-snapshot_date'],
            },
        ),
        
        # Add indexes for performance
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['idempotency_key'], name='wallet_trans_idemp_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['wallet', 'created_at'], name='wallet_trans_wallet_created_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['reference_id'], name='wallet_trans_ref_idx'),
        ),
        migrations.AddIndex(
            model_name='balancesnapshot',
            index=models.Index(fields=['wallet', 'snapshot_date'], name='wallet_snap_wallet_date_idx'),
        ),
    ]
