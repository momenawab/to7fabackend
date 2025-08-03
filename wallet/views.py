from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer, DepositSerializer, WithdrawSerializer
from decimal import Decimal

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_details(request):
    """Get wallet details for the authenticated user"""
    try:
        wallet = Wallet.objects.get(user=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Wallet.DoesNotExist:
        return Response(
            {"error": "Wallet not found for this user"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def deposit_funds(request):
    """Deposit funds to wallet (admin only)"""
    # Get the target user's wallet
    user_id = request.data.get('user_id')
    if not user_id:
        return Response(
            {"error": "user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        wallet = Wallet.objects.get(user_id=user_id)
    except Wallet.DoesNotExist:
        return Response(
            {"error": "Wallet not found for this user"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = DepositSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        
        try:
            # Add admin info to description
            admin_note = f"Deposited by admin: {request.user.email}"
            full_description = f"{description} - {admin_note}" if description else admin_note
            
            wallet.deposit(
                amount=amount,
                description=full_description
            )
            
            # Return updated wallet details
            wallet_serializer = WalletSerializer(wallet)
            return Response({
                "message": f"Successfully deposited {amount} to {wallet.user.email}'s wallet",
                "wallet": wallet_serializer.data
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def withdraw_funds(request):
    """Withdraw funds from wallet (admin only)"""
    # Get the target user's wallet
    user_id = request.data.get('user_id')
    if not user_id:
        return Response(
            {"error": "user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        wallet = Wallet.objects.get(user_id=user_id)
    except Wallet.DoesNotExist:
        return Response(
            {"error": "Wallet not found for this user"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = WithdrawSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        
        try:
            # Add admin info to description
            admin_note = f"Withdrawn by admin: {request.user.email}"
            full_description = f"{description} - {admin_note}" if description else admin_note
            
            wallet.withdraw(
                amount=amount,
                description=full_description
            )
            
            # Return updated wallet details
            wallet_serializer = WalletSerializer(wallet)
            return Response({
                "message": f"Successfully withdrew {amount} from {wallet.user.email}'s wallet",
                "wallet": wallet_serializer.data
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_history(request):
    """Get transaction history for the authenticated user"""
    try:
        wallet = Wallet.objects.get(user=request.user)
        transactions = wallet.transactions.all()
        
        # Optional filtering by transaction type
        transaction_type = request.query_params.get('type')
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
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
        return Response({
            "count": total_count,
            "results": serializer.data
        }, status=status.HTTP_200_OK)
    except Wallet.DoesNotExist:
        return Response(
            {"error": "Wallet not found for this user"},
            status=status.HTTP_404_NOT_FOUND
        )
