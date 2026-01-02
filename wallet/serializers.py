from rest_framework import serializers
from .models import Wallet, Transaction, BalanceSnapshot
import decimal


class TransactionSerializer(serializers.ModelSerializer):
    created_at_formatted = serializers.SerializerMethodField()
    performed_by_email = serializers.SerializerMethodField()
    wallet_user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet', 'wallet_user_email', 'amount', 'transaction_type',
            'reference_id', 'description', 'status', 'balance_before',
            'balance_after', 'idempotency_key', 'performed_by',
            'performed_by_email', 'ip_address', 'user_agent',
            'created_at', 'created_at_formatted'
        ]
        read_only_fields = [
            'id', 'wallet', 'wallet_user_email', 'balance_before',
            'balance_after', 'performed_by', 'performed_by_email',
            'ip_address', 'user_agent', 'created_at', 'created_at_formatted'
        ]
    
    def get_created_at_formatted(self, obj):
        """Return a human-readable date format"""
        return obj.created_at.strftime("%b %d, %Y %H:%M")
    
    def get_performed_by_email(self, obj):
        """Return email of user who performed the transaction"""
        if obj.performed_by:
            return obj.performed_by.email
        return None
    
    def get_wallet_user_email(self, obj):
        """Return email of wallet owner"""
        return obj.wallet.user.email


class WalletSerializer(serializers.ModelSerializer):
    transactions = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'user_id', 'user_email', 'balance',
            'created_at', 'updated_at', 'transactions'
        ]
        read_only_fields = [
            'id', 'user', 'user_id', 'user_email', 'balance',
            'created_at', 'updated_at'
        ]
    
    def get_user_email(self, obj):
        return obj.user.email
    
    def get_user_id(self, obj):
        return obj.user.id
    
    def get_transactions(self, obj):
        # Only include 5 most recent transactions
        recent_transactions = obj.transactions.all()[:5]
        return TransactionSerializer(recent_transactions, many=True).data


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=decimal.Decimal('0.01')
    )
    description = serializers.CharField(required=False, allow_blank=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, max_length=255)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value


class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=decimal.Decimal('0.01')
    )
    description = serializers.CharField(required=False, allow_blank=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, max_length=255)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value
    
    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                wallet = Wallet.objects.get(user=request.user)
                if wallet.balance < data['amount']:
                    raise serializers.ValidationError({"amount": "Insufficient funds"})
            except Wallet.DoesNotExist:
                raise serializers.ValidationError({"user": "Wallet not found"})
        return data


class TransferSerializer(serializers.Serializer):
    target_user_id = serializers.IntegerField()
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=decimal.Decimal('0.01')
    )
    description = serializers.CharField(required=False, allow_blank=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, max_length=255)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value


class BalanceHistorySerializer(serializers.Serializer):
    """Serializer for balance history entries"""
    timestamp = serializers.DateTimeField()
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = serializers.IntegerField()
    transaction_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class BalanceSnapshotSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = BalanceSnapshot
        fields = [
            'id', 'wallet', 'user_email', 'user_id', 'balance',
            'snapshot_date', 'transaction_count'
        ]
        read_only_fields = [
            'id', 'wallet', 'user_email', 'user_id', 'balance',
            'snapshot_date', 'transaction_count'
        ]
    
    def get_user_email(self, obj):
        return obj.wallet.user.email
    
    def get_user_id(self, obj):
        return obj.wallet.user.id
