from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product, CategoryVariantOption
from .ar_models import ARFrameAsset, ProductARSettings, ARPreviewSession
from .ar_serializers import (
    ARFrameAssetSerializer, ProductARSettingsSerializer,
    ARPreviewSessionCreateSerializer, ARFrameCombinationRequestSerializer
)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_ar_settings(request, product_id):
    """Get AR settings for a specific product"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)

        # Check if product supports AR
        if not product.supports_ar:
            return Response({
                'error': 'This product does not support AR preview',
                'supports_ar': False
            }, status=status.HTTP_400_BAD_REQUEST)

        ar_settings = product.ar_settings
        serializer = ProductARSettingsSerializer(ar_settings, context={'request': request})

        return Response({
            'supports_ar': True,
            'product_id': product.id,
            'product_name': product.name,
            'ar_settings': serializer.data
        })

    except Product.DoesNotExist:
        return Response({
            'error': 'Product not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def get_ar_frame_combination(request):
    """Get specific AR frame combination based on variant selections"""
    serializer = ARFrameCombinationRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data

    # Build filter query for AR frame assets
    filter_query = Q(is_active=True)

    frame_type_id = validated_data.get('frame_type_id')
    frame_color_id = validated_data.get('frame_color_id')
    frame_material_id = validated_data.get('frame_material_id')

    if frame_type_id:
        filter_query &= Q(frame_type_variant_id=frame_type_id)

    if frame_color_id:
        filter_query &= Q(frame_color_variant_id=frame_color_id)

    if frame_material_id:
        filter_query &= Q(frame_material_variant_id=frame_material_id)

    # Get matching frame assets
    frame_assets = ARFrameAsset.objects.filter(filter_query)

    if not frame_assets.exists():
        return Response({
            'error': 'No AR frame combination found for the specified variants',
            'available_combinations': 0
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = ARFrameAssetSerializer(frame_assets, many=True, context={'request': request})

    return Response({
        'frame_combinations': serializer.data,
        'total_found': frame_assets.count()
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_ar_frame_variants(request):
    """Get all available frame variants for AR (for building selection UI)"""

    # Get all frame-related variant types that are used in AR
    frame_types = CategoryVariantOption.objects.filter(
        variant_type__name__icontains='frame type',
        is_active=True,
        ar_frame_type_assets__isnull=False
    ).distinct().order_by('variant_type__priority', 'value')

    frame_colors = CategoryVariantOption.objects.filter(
        variant_type__name__icontains='frame color',
        is_active=True,
        ar_frame_color_assets__isnull=False
    ).distinct().order_by('variant_type__priority', 'value')

    frame_materials = CategoryVariantOption.objects.filter(
        variant_type__name__icontains='frame material',
        is_active=True,
        ar_frame_material_assets__isnull=False
    ).distinct().order_by('variant_type__priority', 'value')

    from .ar_serializers import CategoryVariantOptionSerializer

    return Response({
        'frame_types': CategoryVariantOptionSerializer(frame_types, many=True).data,
        'frame_colors': CategoryVariantOptionSerializer(frame_colors, many=True).data,
        'frame_materials': CategoryVariantOptionSerializer(frame_materials, many=True).data
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def create_ar_preview_session(request):
    """Create an AR preview session for analytics"""
    serializer = ARPreviewSessionCreateSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        session = serializer.save()
        return Response({
            'session_id': session.id,
            'message': 'AR preview session created successfully'
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_ar_preview_session(request, session_id):
    """Update AR preview session with user actions"""
    try:
        session = get_object_or_404(ARPreviewSession, id=session_id)

        # Update allowed fields
        update_fields = ['session_duration_seconds', 'photo_saved', 'photo_shared', 'proceeded_to_purchase']

        for field in update_fields:
            if field in request.data:
                setattr(session, field, request.data[field])

        session.save()

        return Response({
            'message': 'AR preview session updated successfully'
        })

    except ARPreviewSession.DoesNotExist:
        return Response({
            'error': 'AR preview session not found'
        }, status=status.HTTP_404_NOT_FOUND)

class ARFrameAssetListView(generics.ListAPIView):
    """List all available AR frame assets"""
    serializer_class = ARFrameAssetSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = ARFrameAsset.objects.filter(is_active=True)

        # Filter by frame type if provided
        frame_type_id = self.request.query_params.get('frame_type_id')
        if frame_type_id:
            queryset = queryset.filter(frame_type_variant_id=frame_type_id)

        # Filter by frame color if provided
        frame_color_id = self.request.query_params.get('frame_color_id')
        if frame_color_id:
            queryset = queryset.filter(frame_color_variant_id=frame_color_id)

        # Filter by frame material if provided
        frame_material_id = self.request.query_params.get('frame_material_id')
        if frame_material_id:
            queryset = queryset.filter(frame_material_variant_id=frame_material_id)

        return queryset.order_by('frame_type_variant__value', 'frame_color_variant__value')

class ProductARSettingsListView(generics.ListAPIView):
    """List all products that support AR"""
    serializer_class = ProductARSettingsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return ProductARSettings.objects.filter(
            ar_enabled=True,
            product__is_active=True,
            product__category__name='لوحات فنية'
        ).select_related('product', 'product__category')

@api_view(['GET'])
@permission_classes([AllowAny])
def ar_analytics(request):
    """Get AR usage analytics"""

    # Basic analytics
    total_sessions = ARPreviewSession.objects.count()
    sessions_with_photos = ARPreviewSession.objects.filter(photo_saved=True).count()
    sessions_with_shares = ARPreviewSession.objects.filter(photo_shared=True).count()
    sessions_with_purchases = ARPreviewSession.objects.filter(proceeded_to_purchase=True).count()

    # Conversion rates
    photo_rate = (sessions_with_photos / total_sessions * 100) if total_sessions > 0 else 0
    share_rate = (sessions_with_shares / total_sessions * 100) if total_sessions > 0 else 0
    conversion_rate = (sessions_with_purchases / total_sessions * 100) if total_sessions > 0 else 0

    # Average session duration
    from django.db.models import Avg
    avg_duration = ARPreviewSession.objects.aggregate(Avg('session_duration_seconds'))['session_duration_seconds__avg'] or 0

    # Most popular frame combinations
    from django.db.models import Count
    popular_frames = ARPreviewSession.objects.values(
        'frame_asset__frame_type_variant__value',
        'frame_asset__frame_color_variant__value'
    ).annotate(count=Count('id')).order_by('-count')[:5]

    return Response({
        'total_sessions': total_sessions,
        'photo_saved_count': sessions_with_photos,
        'photo_shared_count': sessions_with_shares,
        'proceeded_to_purchase_count': sessions_with_purchases,
        'photo_save_rate': round(photo_rate, 2),
        'share_rate': round(share_rate, 2),
        'conversion_rate': round(conversion_rate, 2),
        'average_session_duration_seconds': round(avg_duration, 2),
        'popular_frame_combinations': list(popular_frames)
    })