from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import getpass

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a new admin user or promotes an existing one'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the admin user')
        parser.add_argument('--password', type=str, help='Password for the admin user (if not provided, will prompt)')
        parser.add_argument('--first-name', type=str, help='First name for the admin user')
        parser.add_argument('--last-name', type=str, help='Last name for the admin user')

    def handle(self, *args, **options):
        email = options['email']
        password = options.get('password')
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        
        if not password:
            password = getpass.getpass('Enter password for admin user: ')
            password_confirm = getpass.getpass('Confirm password: ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match'))
                return
        
        try:
            with transaction.atomic():
                user = User.objects.filter(email=email).first()
                
                if user:
                    self.stdout.write(f'User {email} already exists, promoting to admin...')
                    # Update existing user
                    if first_name:
                        user.first_name = first_name
                    if last_name:
                        user.last_name = last_name
                    if password:
                        user.set_password(password)
                else:
                    self.stdout.write(f'Creating new admin user {email}...')
                    # Create new user
                    user = User(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True,
                    )
                    user.set_password(password)
                
                # Make the user a staff member and superuser
                user.is_staff = True
                user.is_superuser = True
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f'Successfully created/promoted {email} to admin status'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating/promoting user: {str(e)}')) 