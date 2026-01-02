from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from api.helpers import api_response, api_error, api_success, api_created
from .models import Wallet, Transaction, BalanceSnapshot
from .serializers import (
    WalletSerializer,
    TransactionSerializer,
    DepositSerializer,
    WithdrawSerializer,
    BalanceHistorySerializer
)
from decimal import Decimal
import uuid


def get_client_info(request):
    """Extract client IP and user agent for audit trail"""
    ip_address = None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    return ip_address, user_agent


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_details(request):
    """
    Get wallet details for authenticated user.
    
    This endpoint is read-only and doesn't require transaction locks.
    """
    try:
        wallet = Wallet.objects.get(user=request.user)
        serializer = WalletSerializer(wallet)
        return api_success(request, data=serializer.data)
    except Wallet.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Wallet not found for this user",
            status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def deposit_funds(request):
    """
    Deposit funds to wallet (admin only).
    
    This operation is concurrency-safe using select_for_update() locking.
    Supports idempotency to prevent duplicate deposits.
    """
    # Get the target user's wallet
    user_id = request.data.get('user_id')
    if not user_id:
        return api_error(
            request,
            code='VALIDATION_ERROR',
            message="user_id is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        wallet = Wallet.objects.get(user_id=user_id)
    except Wallet.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Wallet not found for this user",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    serializer = DepositSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        
        try:
            # Generate idempotency key if not provided
            idempotency_key = request.data.get('idempotency_key')
            if not idempotency_key:
                idempotency_key = f"deposit_{user_id}_{uuid.uuid4()}"
            
            # Add admin info to description
            admin_note = f"Deposited by admin: {request.user.email}"
            full_description = f"{description} - {admin_note}" if description else admin_note
            
            # Extract client info BEFORE calling deposit (for audit trail)
            ip_address, user_agent = get_client_info(request)
            
            # Perform deposit with idempotency and audit trail
            # All audit fields are populated within the atomic transaction
            tx = wallet.deposit(
                amount=amount,
                description=full_description,
                idempotency_key=idempotency_key,
                performed_by=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Return updated wallet details
            wallet_serializer = WalletSerializer(wallet)
            return api_success(request, data={
                "wallet": wallet_serializer.data,
                "transaction": TransactionSerializer(tx).data,
                "idempotency_key": idempotency_key
            }, message=f"Successfully deposited {amount} to {wallet.user.email}'s wallet")
        except ValueError as e:
            return api_error(
                request,
                code='TRANSACTION_ERROR',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    return api_error(
        request,
        code='VALIDATION_ERROR',
        message='Validation failed',
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def withdraw_funds(request):
    """
    Withdraw funds from wallet (admin only).
    
    This operation is concurrency-safe using select_for_update() locking.
    Prevents negative balances and supports idempotency.
    """
    # Get the target user's wallet
    user_id = request.data.get('user_id')
    if not user_id:
        return api_error(
            request,
            code='VALIDATION_ERROR',
            message="user_id is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        wallet = Wallet.objects.get(user_id=user_id)
    except Wallet.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Wallet not found for this user",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    serializer = WithdrawSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        
        try:
            # Generate idempotency key if not provided
            idempotency_key = request.data.get('idempotency_key')
            if not idempotency_key:
                idempotency_key = f"withdraw_{user_id}_{uuid.uuid4()}"
            
            # Add admin info to description
            admin_note = f"Withdrawn by admin: {request.user.email}"
            full_description = f"{description} - {admin_note}" if description else admin_note
            
            # Extract client info BEFORE calling withdraw (for audit trail)
            ip_address, user_agent = get_client_info(request)
            
            # Perform withdrawal with idempotency and audit trail
            # All audit fields are populated within the atomic transaction
            tx = wallet.withdraw(
                amount=amount,
                description=full_description,
                idempotency_key=idempotency_key,
                performed_by=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Return updated wallet details
            wallet_serializer = WalletSerializer(wallet)
            return api_success(request, data={
                "wallet": wallet_serializer.data,
                "transaction": TransactionSerializer(tx).data,
                "idempotency_key": idempotency_key
            }, message=f"Successfully withdrew {amount} from {wallet.user.email}'s wallet")
        except ValueError as e:
            return api_error(
                request,
                code='TRANSACTION_ERROR',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    return api_error(
        request,
        code='VALIDATION_ERROR',
        message='Validation failed',
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_funds(request):
    """
    Transfer funds from one wallet to another.
    
    This operation is fully atomic - either both transactions succeed or both fail.
    Uses select_for_update() on both wallets to prevent race conditions.
    Supports idempotency to prevent duplicate transfers.
    """
    target_user_id = request.data.get('target_user_id')
    amount = request.data.get('amount')
    description = request.data.get('description', '')
    
    if not target_user_id:
        return api_error(
            request,
            code='VALIDATION_ERROR',
            message="target_user_id is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    if not amount:
        return api_error(
            request,
            code='VALIDATION_ERROR',
            message="amount is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        amount = Decimal(str(amount))
    except (ValueError, TypeError):
        return api_error(
            request,
            code='INVALID_AMOUNT',
            message="Invalid amount format",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    if amount <= 0:
        return api_error(
            request,
            code='INVALID_AMOUNT',
            message="Amount must be positive",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Get source wallet
    try:
        source_wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Wallet not found for current user",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Get target wallet
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target_user = User.objects.get(id=target_user_id)
        target_wallet = Wallet.objects.get(user=target_user)
    except User.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Target user not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Wallet.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Target wallet not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Generate idempotency key if not provided
        idempotency_key = request.data.get('idempotency_key')
        if not idempotency_key:
            idempotency_key = f"transfer_{request.user.id}_{target_user_id}_{uuid.uuid4()}"
        
        # Extract client info BEFORE calling transfer (for audit trail)
        ip_address, user_agent = get_client_info(request)
        
        # Perform transfer with idempotency and audit trail
        # All audit fields are populated within the atomic transaction
        withdrawal_tx, deposit_tx = source_wallet.transfer(
            amount=amount,
            target_wallet=target_wallet,
            description=description or f"Transfer to {target_user.email}",
            idempotency_key=idempotency_key,
            performed_by=request.user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Return updated wallet details
        source_serializer = WalletSerializer(source_wallet)
        target_serializer = WalletSerializer(target_wallet)
        
        return api_success(request, data={
            "source_wallet": source_serializer.data,
            "target_wallet": target_serializer.data,
            "withdrawal_transaction": TransactionSerializer(withdrawal_tx).data,
            "deposit_transaction": TransactionSerializer(deposit_tx).data,
            "idempotency_key": idempotency_key
        }, message=f"Successfully transferred {amount} to {target_user.email}")
    except ValueError as e:
        return api_error(
            request,
            code='TRANSACTION_ERROR',
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_history(request):
    """
    Get transaction history for authenticated user.
    
    Supports filtering by transaction type, date range, and pagination.
    """
    try:
        wallet = Wallet.objects.get(user=request.user)
        transactions = wallet.transactions.all()
        
        # Optional filtering by transaction type
        transaction_type = request.query_params.get('type')
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Optional filtering by status
        tx_status = request.query_params.get('status')
        if tx_status:
            transactions = transactions.filter(status=tx_status)
        
        # Optional date range filtering
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            transactions = transactions.filter(created_at__date__gte=date_from)
        if date_to:
            transactions = transactions.filter(created_at__date__lte=date_to)
        
        # Pagination
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        # Get total count before pagination
        total_count = transactions.count()
        
        # Apply pagination
        transactions = transactions[offset:offset+limit]
        
        serializer = TransactionSerializer(transactions, many=True)
        return api_success(request, data={
            "count": total_count,
            "results": serializer.data
        })
    except Wallet.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Wallet not found for this user",
            status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def balance_history(request):
    """
    Get balance history for authenticated user.
    
    This endpoint provides a historical view of balance changes over time.
    It calculates the running balance from all transactions in chronological order.
    
    Query Parameters:
        - date_from: Optional start date (YYYY-MM-DD)
        - date_to: Optional end date (YYYY-MM-DD)
        - limit: Number of records to return (default: 100)
        - offset: Number of records to skip (default: 0)
    """
    try:
        wallet = Wallet.objects.get(user=request.user)
        
        # Get filter parameters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        
        # Get balance history
        history = Wallet.get_balance_history(
            wallet_id=wallet.id,
            start_date=date_from,
            end_date=date_to
        )
        
        # Apply pagination
        total_count = len(history)
        history = history[offset:offset+limit]
        
        serializer = BalanceHistorySerializer(history, many=True)
        return api_success(request, data={
            "count": total_count,
            "results": serializer.data,
            "current_balance": str(wallet.balance)
        })
    except Wallet.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Wallet not found for this user",
            status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def all_transactions(request):
    """
    Get all transactions across all wallets (admin only).
    
    Supports filtering by user, transaction type, status, date range, and pagination.
    """
    transactions = Transaction.objects.all()
    
    # Filter by user
    user_id = request.query_params.get('user_id')
    if user_id:
        transactions = transactions.filter(wallet__user_id=user_id)
    
    # Filter by transaction type
    transaction_type = request.query_params.get('type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Filter by status
    tx_status = request.query_params.get('status')
    if tx_status:
        transactions = transactions.filter(status=tx_status)
    
    # Filter by reference ID
    reference_id = request.query_params.get('reference_id')
    if reference_id:
        transactions = transactions.filter(reference_id=reference_id)
    
    # Date range filtering
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)
    
    # Pagination
    limit = int(request.query_params.get('limit', 50))
    offset = int(request.query_params.get('offset', 0))
    
    # Get total count before pagination
    total_count = transactions.count()
    
    # Apply pagination
    transactions = transactions[offset:offset+limit]
    
    serializer = TransactionSerializer(transactions, many=True)
    return api_success(request, data={
        "count": total_count,
        "results": serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_detail(request, transaction_id):
    """
    Get details of a specific transaction.
    
    Users can only view their own transactions.
    Admins can view any transaction.
    """
    try:
        if request.user.is_staff:
            transaction = Transaction.objects.get(id=transaction_id)
        else:
            wallet = Wallet.objects.get(user=request.user)
            transaction = Transaction.objects.get(id=transaction_id, wallet=wallet)
        
        serializer = TransactionSerializer(transaction)
        return api_success(request, data=serializer.data)
    except Transaction.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Transaction not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Wallet.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Wallet not found for this user",
            status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_balance_snapshot(request):
    """
    Create a balance snapshot for a wallet (admin only).
    
    This is useful for periodic balance reporting and historical analysis.
    """
    user_id = request.data.get('user_id')
    if not user_id:
        return api_error(
            request,
            code='VALIDATION_ERROR',
            message="user_id is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        wallet = Wallet.objects.get(user_id=user_id)
    except Wallet.DoesNotExist:
        return api_error(
            request,
            code='NOT_FOUND',
            message="Wallet not found for this user",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Count total transactions
    transaction_count = wallet.transactions.count()
    
    # Create snapshot
    snapshot = BalanceSnapshot.objects.create(
        wallet=wallet,
        balance=wallet.balance,
        transaction_count=transaction_count
    )
    
    return api_created(request, data={
        "snapshot": {
            "id": snapshot.id,
            "wallet": wallet.user.email,
            "balance": str(snapshot.balance),
            "transaction_count": snapshot.transaction_count,
            "snapshot_date": snapshot.snapshot_date
        }
    }, message="Balance snapshot created successfully")
