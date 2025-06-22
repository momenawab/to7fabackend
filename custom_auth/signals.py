from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Customer, Artist, Store

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create the appropriate profile when a user is created
    """
    if created:
        if instance.user_type == 'customer':
            Customer.objects.create(user=instance)
        elif instance.user_type == 'artist':
            Artist.objects.create(user=instance)
        elif instance.user_type == 'store':
            Store.objects.create(user=instance, store_name=f"{instance.email}'s Store")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save the appropriate profile when a user is updated
    """
    if instance.user_type == 'customer':
        if hasattr(instance, 'customer_profile'):
            instance.customer_profile.save()
        else:
            Customer.objects.create(user=instance)
    elif instance.user_type == 'artist':
        if hasattr(instance, 'artist_profile'):
            instance.artist_profile.save()
        else:
            Artist.objects.create(user=instance)
    elif instance.user_type == 'store':
        if hasattr(instance, 'store_profile'):
            instance.store_profile.save()
        else:
            Store.objects.create(user=instance, store_name=f"{instance.email}'s Store") 