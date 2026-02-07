"""
Cart Services

This module contains business logic for cart operations,
including guest cart management and cart merging.
"""

from .cart_merge import merge_guest_cart

__all__ = [
    "merge_guest_cart",
]
