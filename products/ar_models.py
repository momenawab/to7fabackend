from django.db import models
from django.conf import settings

class ARFrameAsset(models.Model):
    """Maps variant combinations to 3D frame assets for AR visualization"""

    # Variant mapping - link to existing variant options
    frame_type_variant = models.ForeignKey(
        'CategoryVariantOption',
        on_delete=models.CASCADE,
        related_name='ar_frame_type_assets',
        help_text="Frame type variant option (e.g., Classic, Modern, Gallery)"
    )
    frame_color_variant = models.ForeignKey(
        'CategoryVariantOption',
        on_delete=models.CASCADE,
        related_name='ar_frame_color_assets',
        help_text="Frame color variant option (e.g., Black, White, Gold)"
    )
    frame_material_variant = models.ForeignKey(
        'CategoryVariantOption',
        on_delete=models.CASCADE,
        related_name='ar_frame_material_assets',
        blank=True,
        null=True,
        help_text="Frame material variant option (optional - e.g., Wood, Metal)"
    )

    # 3D Asset files for AR
    frame_3d_model = models.FileField(
        upload_to='ar_frames/models/',
        help_text="3D model file (.obj, .fbx, .glb) for this frame variant combination"
    )
    frame_texture = models.ImageField(
        upload_to='ar_frames/textures/',
        blank=True,
        null=True,
        help_text="Texture image for the frame material"
    )
    frame_preview_image = models.ImageField(
        upload_to='ar_frames/previews/',
        help_text="Preview image showing how this frame looks"
    )

    # Frame physical properties
    frame_width_cm = models.FloatField(default=3.0, help_text="Frame width in centimeters")
    frame_depth_cm = models.FloatField(default=2.0, help_text="Frame depth in centimeters")

    # AR-specific settings
    scale_factor = models.FloatField(default=1.0, help_text="Scale factor for 3D model in AR")
    position_offset_x = models.FloatField(default=0.0, help_text="X-axis position offset")
    position_offset_y = models.FloatField(default=0.0, help_text="Y-axis position offset")
    position_offset_z = models.FloatField(default=0.0, help_text="Z-axis position offset")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        material = f" - {self.frame_material_variant.value}" if self.frame_material_variant else ""
        return f"{self.frame_type_variant.value} {self.frame_color_variant.value}{material} Frame"

    class Meta:
        unique_together = ['frame_type_variant', 'frame_color_variant', 'frame_material_variant']
        verbose_name = 'AR Frame Asset'
        verbose_name_plural = 'AR Frame Assets'


class ProductARSettings(models.Model):
    """AR-specific settings for products that support AR preview"""

    product = models.OneToOneField('Product', on_delete=models.CASCADE, related_name='ar_settings')

    # Enable/disable AR for this product
    ar_enabled = models.BooleanField(default=False, help_text="Enable AR preview for this product")

    # Artwork dimensions (needed for proper scaling in AR)
    artwork_width_cm = models.FloatField(help_text="Artwork width in centimeters")
    artwork_height_cm = models.FloatField(help_text="Artwork height in centimeters")

    # Artwork properties
    artwork_orientation = models.CharField(
        max_length=20,
        choices=[
            ('landscape', 'Landscape'),
            ('portrait', 'Portrait'),
            ('square', 'Square')
        ],
        default='landscape'
    )

    # Default frame selection (if any)
    default_frame_type = models.ForeignKey(
        'CategoryVariantOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_frame_products',
        help_text="Default frame type for AR preview"
    )
    default_frame_color = models.ForeignKey(
        'CategoryVariantOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_color_products',
        help_text="Default frame color for AR preview"
    )

    # AR experience settings
    min_distance_meters = models.FloatField(default=0.5, help_text="Minimum viewing distance in meters")
    max_distance_meters = models.FloatField(default=5.0, help_text="Maximum viewing distance in meters")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AR Settings for {self.product.name}"

    def get_available_frame_combinations(self):
        """Get all available frame combinations for this product's variants"""
        if not self.product.category or not self.ar_enabled:
            return ARFrameAsset.objects.none()

        # Get all frame assets that match this product's available variant options
        product_variants = self.product.selected_variants.all()

        # Extract variant option IDs for frame types and colors
        frame_type_ids = []
        frame_color_ids = []
        frame_material_ids = []

        for variant in product_variants:
            option = variant.category_variant_option
            variant_type_name = option.variant_type.name.lower()

            if 'frame' in variant_type_name and 'type' in variant_type_name:
                frame_type_ids.append(option.id)
            elif 'frame' in variant_type_name and 'color' in variant_type_name:
                frame_color_ids.append(option.id)
            elif 'frame' in variant_type_name and 'material' in variant_type_name:
                frame_material_ids.append(option.id)

        # Filter AR frame assets by available combinations
        queryset = ARFrameAsset.objects.filter(is_active=True)

        if frame_type_ids:
            queryset = queryset.filter(frame_type_variant_id__in=frame_type_ids)
        if frame_color_ids:
            queryset = queryset.filter(frame_color_variant_id__in=frame_color_ids)
        if frame_material_ids:
            queryset = queryset.filter(frame_material_variant_id__in=frame_material_ids)

        return queryset

    @property
    def aspect_ratio(self):
        """Calculate artwork aspect ratio"""
        if self.artwork_height_cm > 0:
            return self.artwork_width_cm / self.artwork_height_cm
        return 1.0

    class Meta:
        verbose_name = 'Product AR Settings'
        verbose_name_plural = 'Product AR Settings'


class ARPreviewSession(models.Model):
    """Track AR preview sessions for analytics"""

    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='ar_sessions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # Session details
    frame_asset = models.ForeignKey(ARFrameAsset, on_delete=models.CASCADE, related_name='preview_sessions')
    session_duration_seconds = models.PositiveIntegerField(default=0)

    # Device info
    device_model = models.CharField(max_length=100, blank=True)
    platform = models.CharField(max_length=20, choices=[('android', 'Android'), ('ios', 'iOS')], blank=True)

    # Actions taken
    photo_saved = models.BooleanField(default=False)
    photo_shared = models.BooleanField(default=False)
    proceeded_to_purchase = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_info = f" by {self.user.email}" if self.user else " (anonymous)"
        return f"AR Preview: {self.product.name}{user_info}"

    class Meta:
        verbose_name = 'AR Preview Session'
        verbose_name_plural = 'AR Preview Sessions'