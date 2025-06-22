from rest_framework import serializers
from .models import Wallet, Transaction
import decimal

class TransactionSerializer(serializers.ModelSerializer):
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'transaction_type', 'reference_id',
            'description', 'status', 'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['id', 'created_at', 'created_at_formatted']
    
    def get_created_at_formatted(self, obj):
        """Return a human-readable date format"""
        return obj.created_at.strftime("%b %d, %Y %H:%M")

class WalletSerializer(serializers.ModelSerializer):
    transactions = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'user_email', 'balance', 'created_at', 'updated_at', 'transactions']
        read_only_fields = ['id', 'user', 'user_email', 'balance', 'created_at', 'updated_at']
    
    def get_user_email(self, obj):
        return obj.user.email
    
    def get_transactions(self, obj):
        # Only include the 5 most recent transactions
        recent_transactions = obj.transactions.all()[:5]
        return TransactionSerializer(recent_transactions, many=True).data

class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=decimal.Decimal('0.01'))
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value

class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=decimal.Decimal('0.01'))
    description = serializers.CharField(required=False, allow_blank=True)
    
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