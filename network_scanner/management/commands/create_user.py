from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Create a new user account for the system'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the new user')
        parser.add_argument('email', type=str, help='Email address for the new user')
        parser.add_argument('password', type=str, help='Password for the new user')
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Create a superuser account',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        is_superuser = options['superuser']

        # Check if user dah ada
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'User "{username}" already exists!')
            )
            return

        try:
            if is_superuser:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Superuser "{username}" created successfully!')
                )
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'User "{username}" created successfully!')
                )

            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Superuser: {is_superuser}')

        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Validation error: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {e}')
            )

