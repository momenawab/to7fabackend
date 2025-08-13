from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .address_models import UserAddress
from .address_serializers import (
    UserAddressSerializer, 
    AddressCreateSerializer,
    AddressUpdateSerializer
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_addresses(request):
    """
    Get all addresses for the authenticated user
    """
    addresses = UserAddress.objects.filter(user=request.user)
    serializer = UserAddressSerializer(addresses, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_address(request):
    """
    Create a new address for the authenticated user
    """
    print(f"Received data: {request.data}")  # Debug print
    serializer = AddressCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        address = serializer.save()
        response_serializer = UserAddressSerializer(address)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    print(f"Serializer errors: {serializer.errors}")  # Debug print
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_address(request, address_id):
    """
    Get a specific address by ID (only if it belongs to the user)
    """
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    serializer = UserAddressSerializer(address)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_address(request, address_id):
    """
    Update a specific address (only if it belongs to the user)
    """
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    
    partial = request.method == 'PATCH'
    serializer = AddressUpdateSerializer(address, data=request.data, partial=partial)
    
    if serializer.is_valid():
        address = serializer.save()
        response_serializer = UserAddressSerializer(address)
        return Response(response_serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_address(request, address_id):
    """
    Delete a specific address (only if it belongs to the user)
    """
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    
    # If deleting the default address, set another address as default
    if address.is_default:
        other_address = UserAddress.objects.filter(user=request.user).exclude(id=address_id).first()
        if other_address:
            other_address.is_default = True
            other_address.save()
    
    address.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_default_address(request, address_id):
    """
    Set a specific address as the default address
    """
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    
    # Remove default from all user addresses
    UserAddress.objects.filter(user=request.user).update(is_default=False)
    
    # Set this address as default
    address.is_default = True
    address.save()
    
    serializer = UserAddressSerializer(address)
    return Response(serializer.data)