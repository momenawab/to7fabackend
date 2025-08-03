from django.contrib import admin
from .models import Wallet, Transaction

class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('amount', 'transaction_type', 'reference_id', 'description', 'status', 'created_at')
    
    def has_add_permission(self, request, obj=None):
        return False

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TransactionInline]

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'transaction_type', 'status', 'created_at')
    list_filter = ('transaction_type', 'status')
    search_fields = ('wallet__user__email', 'reference_id', 'description')
    readonly_fields = ('created_at',)

admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)
