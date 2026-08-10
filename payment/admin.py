from django.contrib import admin
from .models import PaymentMethod, Payment, PaymentAttempt, GatewayTransaction, Refund, WebhookEvent


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'is_default', 'created_at')
    list_filter = ('method_type', 'is_default')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)


class PaymentAttemptInline(admin.TabularInline):
    model = PaymentAttempt
    extra = 0
    readonly_fields = ('status', 'gateway_reference', 'failure_reason', 'created_at', 'updated_at')
    can_delete = False


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ('amount', 'status', 'gateway_refund_id', 'requested_by', 'created_at')
    can_delete = False


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'amount', 'gateway', 'status', 'amount_refunded', 'created_at')
    list_filter = ('status', 'gateway')
    search_fields = ('order__id', 'user__email', 'idempotency_key')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PaymentAttemptInline, RefundInline]

    fieldsets = (
        ('Payment', {
            'fields': ('order', 'user', 'gateway', 'amount', 'currency', 'status', 'amount_refunded', 'idempotency_key')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class GatewayTransactionAdmin(admin.ModelAdmin):
    list_display = ('gateway_transaction_id', 'attempt', 'is_success', 'amount', 'created_at')
    list_filter = ('is_success',)
    search_fields = ('gateway_transaction_id',)
    readonly_fields = ('created_at',)


class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('gateway', 'event_id', 'signature_valid', 'processed', 'received_at')
    list_filter = ('gateway', 'signature_valid', 'processed')
    search_fields = ('event_id',)
    readonly_fields = ('received_at',)


admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(GatewayTransaction, GatewayTransactionAdmin)
admin.site.register(WebhookEvent, WebhookEventAdmin)
