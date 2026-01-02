from django.db import models, transaction
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s wallet"
    
    @transaction.atomic
    def deposit(self, amount, reference_id=None, description=None, idempotency_key=None,
                performed_by=None, ip_address=None, user_agent=None):
        """
        Add funds to wallet and create a transaction record.
        
        This method is concurrency-safe using select_for_update() which locks the wallet row
        until the transaction completes, preventing race conditions.
        
        Args:
            amount: Positive decimal amount to deposit
            reference_id: Optional reference (order ID, payment ID, etc.)
            description: Optional description of the transaction
            idempotency_key: Unique key to prevent duplicate transactions
            performed_by: User who performed the transaction (for audit trail)
            ip_address: Client IP address (for audit trail)
            user_agent: Client user agent string (for audit trail)
            
        Returns:
            Transaction object if successful
            
        Raises:
            ValueError: If amount is not positive or idempotency_key already exists
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Check for idempotency - prevent duplicate transactions
        if idempotency_key:
            if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
                existing_tx = Transaction.objects.get(idempotency_key=idempotency_key)
                return existing_tx
        
        # Lock the wallet row for update to prevent concurrent modifications
        # This ensures that only one transaction can modify the balance at a time
        wallet = Wallet.objects.select_for_update().get(id=self.id)
        
        # Capture balance before transaction for audit trail
        balance_before = wallet.balance
        balance_after = balance_before + amount
        
        # Update balance
        wallet.balance = balance_after
        wallet.save()
        
        # Create transaction record with full audit trail (all fields populated within transaction)
        tx = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='deposit',
            reference_id=reference_id,
            description=description or f"Deposit of {amount}",
            status='completed',
            balance_before=balance_before,
            balance_after=balance_after,
            idempotency_key=idempotency_key,
            performed_by=performed_by,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return tx
    
    @transaction.atomic
    def withdraw(self, amount, reference_id=None, description=None, idempotency_key=None,
                 performed_by=None, ip_address=None, user_agent=None):
        """
        Withdraw funds from wallet and create a transaction record.
        
        This method is concurrency-safe using select_for_update() which locks the wallet row
        until the transaction completes, preventing race conditions and negative balances.
        
        Args:
            amount: Positive decimal amount to withdraw
            reference_id: Optional reference (order ID, payment ID, etc.)
            description: Optional description of the transaction
            idempotency_key: Unique key to prevent duplicate transactions
            performed_by: User who performed the transaction (for audit trail)
            ip_address: Client IP address (for audit trail)
            user_agent: Client user agent string (for audit trail)
            
        Returns:
            Transaction object if successful
            
        Raises:
            ValueError: If amount is not positive, insufficient funds, or idempotency_key already exists
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Check for idempotency - prevent duplicate transactions
        if idempotency_key:
            if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
                existing_tx = Transaction.objects.get(idempotency_key=idempotency_key)
                return existing_tx
        
        # Lock the wallet row for update to prevent concurrent modifications
        wallet = Wallet.objects.select_for_update().get(id=self.id)
        
        # Capture balance before transaction for audit trail
        balance_before = wallet.balance
        
        # Prevent negative balances - check AFTER acquiring lock
        if balance_before < amount:
            raise ValueError("Insufficient funds")
        
        balance_after = balance_before - amount
        
        # Update balance
        wallet.balance = balance_after
        wallet.save()
        
        # Create transaction record with full audit trail (all fields populated within transaction)
        tx = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='withdrawal',
            reference_id=reference_id,
            description=description or f"Withdrawal of {amount}",
            status='completed',
            balance_before=balance_before,
            balance_after=balance_after,
            idempotency_key=idempotency_key,
            performed_by=performed_by,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return tx
    
    @transaction.atomic
    def transfer(self, amount, target_wallet, reference_id=None, description=None, idempotency_key=None,
                performed_by=None, ip_address=None, user_agent=None):
        """
        Transfer funds from this wallet to another wallet.
        
        This method is fully atomic - either both transactions succeed or both fail.
        Uses select_for_update() on both wallets to prevent race conditions.
        
        Args:
            amount: Positive decimal amount to transfer
            target_wallet: Wallet object to transfer funds to
            reference_id: Optional reference (order ID, payment ID, etc.)
            description: Optional description of the transaction
            idempotency_key: Unique key to prevent duplicate transactions
            performed_by: User who performed the transaction (for audit trail)
            ip_address: Client IP address (for audit trail)
            user_agent: Client user agent string (for audit trail)
            
        Returns:
            Tuple of (withdrawal_transaction, deposit_transaction) if successful
            
        Raises:
            ValueError: If amount is not positive, insufficient funds, or idempotency_key already exists
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if self.id == target_wallet.id:
            raise ValueError("Cannot transfer to the same wallet")
        
        # Check for idempotency - prevent duplicate transactions
        if idempotency_key:
            if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
                existing_tx = Transaction.objects.filter(idempotency_key=idempotency_key)
                withdrawal_tx = existing_tx.filter(transaction_type='withdrawal').first()
                deposit_tx = existing_tx.filter(transaction_type='deposit').first()
                return (withdrawal_tx, deposit_tx)
        
        # Lock both wallets to prevent concurrent modifications
        # Always lock in a consistent order (by ID) to prevent deadlocks
        wallets_to_lock = sorted([self, target_wallet], key=lambda w: w.id)
        locked_wallets = list(Wallet.objects.select_for_update().filter(id__in=[w.id for w in wallets_to_lock]))
        
        source_wallet = next(w for w in locked_wallets if w.id == self.id)
        dest_wallet = next(w for w in locked_wallets if w.id == target_wallet.id)
        
        # Capture balances before transaction
        source_balance_before = source_wallet.balance
        dest_balance_before = dest_wallet.balance
        
        # Prevent negative balances
        if source_balance_before < amount:
            raise ValueError("Insufficient funds")
        
        source_balance_after = source_balance_before - amount
        dest_balance_after = dest_balance_before + amount
        
        # Update both balances
        source_wallet.balance = source_balance_after
        dest_wallet.balance = dest_balance_after
        source_wallet.save()
        dest_wallet.save()
        
        # Create transaction records with full audit trail (all fields populated within transaction)
        withdrawal_tx = Transaction.objects.create(
            wallet=source_wallet,
            amount=amount,
            transaction_type='withdrawal',
            reference_id=reference_id,
            description=description or f"Transfer to {dest_wallet.user.email}",
            status='completed',
            balance_before=source_balance_before,
            balance_after=source_balance_after,
            idempotency_key=idempotency_key,
            performed_by=performed_by,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        deposit_tx = Transaction.objects.create(
            wallet=dest_wallet,
            amount=amount,
            transaction_type='deposit',
            reference_id=reference_id,
            description=description or f"Transfer from {source_wallet.user.email}",
            status='completed',
            balance_before=dest_balance_before,
            balance_after=dest_balance_after,
            idempotency_key=idempotency_key,
            performed_by=performed_by,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return (withdrawal_tx, deposit_tx)
    
    @classmethod
    def get_balance_history(cls, wallet_id, start_date=None, end_date=None):
        """
        Get balance snapshots for a wallet over time.
        
        This provides a historical view of balance changes by analyzing transactions.
        
        Args:
            wallet_id: ID of the wallet
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List of dictionaries with timestamp and balance
        """
        from decimal import Decimal
        
        transactions = Transaction.objects.filter(wallet_id=wallet_id).order_by('created_at')
        
        if start_date:
            transactions = transactions.filter(created_at__gte=start_date)
        if end_date:
            transactions = transactions.filter(created_at__lte=end_date)
        
        history = []
        running_balance = Decimal('0.00')
        
        for tx in transactions:
            if tx.transaction_type in ['deposit', 'refund']:
                running_balance += tx.amount
            elif tx.transaction_type in ['withdrawal', 'payment', 'commission']:
                running_balance -= tx.amount
            
            history.append({
                'timestamp': tx.created_at,
                'balance': running_balance,
                'transaction_id': tx.id,
                'transaction_type': tx.transaction_type,
                'amount': tx.amount
            })
        
        return history


class Transaction(models.Model):
    TYPE_CHOICES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('commission', 'Commission'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    reference_id = models.CharField(max_length=100, blank=True, null=True)  # Order ID, Payment ID, etc.
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    # Audit trail fields
    balance_before = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    
    # Additional audit fields
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_transactions'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.wallet.user.email}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['reference_id']),
        ]
    
    def clean(self):
        """Validate transaction data"""
        if self.balance_before is not None and self.balance_after is not None:
            # Verify balance change matches transaction type and amount
            if self.transaction_type in ['deposit', 'refund']:
                expected_after = self.balance_before + self.amount
            elif self.transaction_type in ['withdrawal', 'payment', 'commission']:
                expected_after = self.balance_before - self.amount
            else:
                expected_after = self.balance_after
            
            if self.balance_after != expected_after:
                raise ValidationError({
                    'balance_after': f'Balance after ({self.balance_after}) does not match expected ({expected_after})'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class BalanceSnapshot(models.Model):
    """
    Periodic balance snapshots for historical analysis and reporting.
    
    This model stores periodic snapshots of wallet balances to provide
    efficient balance history queries without recalculating from all transactions.
    """
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='balance_snapshots')
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    snapshot_date = models.DateTimeField(auto_now_add=True)
    transaction_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['wallet', 'snapshot_date']),
        ]
        verbose_name = 'Balance Snapshot'
        verbose_name_plural = 'Balance Snapshots'
    
    def __str__(self):
        return f"{self.wallet.user.email} - {self.balance} at {self.snapshot_date}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet(sender, instance, created, **kwargs):
    """Create a wallet for each new user"""
    if created:
        Wallet.objects.create(user=instance)
