from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Promotes a user to admin status by email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user to promote')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            with transaction.atomic():
                user = User.objects.filter(email=email).first()
                
                if not user:
                    self.stdout.write(self.style.ERROR(f'User with email {email} does not exist'))
                    return
                
                # Make the user a staff member and superuser
                user.is_staff = True
                user.is_superuser = True
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f'Successfully promoted {email} to admin status'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error promoting user: {str(e)}')) 