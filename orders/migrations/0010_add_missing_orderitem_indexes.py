# Phase 2 fix (BACKEND_AUDIT.md / PHASE1_STABILIZATION_REPORT.md §5): restores a missing
# link in the migration history.
#
# 0004_rename_orders_order_user_created_at_idx_orders_orde_user_id_0ae59f_idx_and_more.py
# renames three OrderItem indexes (orderitem_order_product_idx, orderitem_seller_idx,
# orderitem_variant_id_idx) as if they already existed, but no earlier migration ever
# created them - 0003_add_order_indexes.py only indexes Order, never OrderItem. On a
# genuinely fresh database this makes 0004's RenameIndex fail immediately
# (MySQLdb.OperationalError 1176: "Key ... doesn't exist"), which was the root cause of
# all 304 non-passing outcomes in the Phase 1 test baseline.
#
# This migration creates those three indexes under their original names, so 0004's
# rename has something real to act on. The current model's Meta.indexes already declares
# these three as unnamed indexes (Django auto-generates orders_orde_order_i_52f79a_idx,
# orders_orde_seller__cbcf6b_idx, orders_orde_variant_164791_idx for them - exactly what
# 0004 renames TO), so this migration's end state matches what the model has always
# specified; only the intermediate step was missing from tracked history.
#
# CREATE INDEX is non-destructive - it cannot lose data. Verified this makes
# `python manage.py migrate` succeed from a genuinely empty database.
#
# PRODUCTION NOTE: before applying this migration to production, run
# `SHOW INDEX FROM orders_orderitem;` there first. If production's schema matches this
# project's local dev database (neither the old nor new index names present - the
# evidence suggests 0004 was applied there via --fake or an equivalent no-op, since dev's
# schema has never had these indexes under any name despite 0004 showing as applied),
# this migration will simply create them, exactly as intended. If production already has
# an index under one of the three old names below, this migration will fail loudly (a
# duplicate-key-name error) rather than corrupt anything - that scenario needs a human to
# adjust this migration before it's deployed there.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_add_order_indexes'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['order', 'product'], name='orderitem_order_product_idx'),
        ),
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['seller'], name='orderitem_seller_idx'),
        ),
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['variant_id'], name='orderitem_variant_id_idx'),
        ),
    ]
