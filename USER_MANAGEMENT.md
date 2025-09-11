# User Management Guide

## Overview
The Etiqa NetConfig Saver application requires user authentication. Username and password credentials can only be created through the system administrator interface.

## Creating Users

### Method 1: Django Admin Interface (Recommended)
1. Access the Django admin interface at `/admin/`
2. Login with superuser credentials
3. Navigate to "Users" section
4. Click "Add user" to create new users
5. Set username, email, and password
6. Choose user permissions (staff, superuser, etc.)

### Method 2: Management Command
Use the custom management command to create users from the command line:

```bash
# Create a regular user
python manage.py create_user username email@example.com password123

# Create a superuser
python manage.py create_user admin admin@etiqa.com admin123 --superuser
```

### Method 3: Django Shell
For advanced users, you can create users programmatically:

```python
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.create_user('username', 'email@example.com', 'password')
>>> User.objects.create_superuser('admin', 'admin@etiqa.com', 'password')
```

## Default Credentials

### Superuser Account
- **Username:** `admin`
- **Password:** Contact system administrator
- **Access:** Full system access including Django admin

### Test User Account
- **Username:** `testuser`
- **Password:** `testpass123`
- **Access:** Regular user access to application features

## Security Notes

1. **Change Default Passwords:** Always change default passwords in production
2. **Strong Passwords:** Use strong, unique passwords for all accounts
3. **Regular Audits:** Regularly review and audit user accounts
4. **Access Control:** Only create accounts for authorized personnel
5. **Admin Access:** Limit superuser accounts to essential personnel only

## User Permissions

### Regular Users
- Access to backup dashboard
- View and manage network configurations
- Download backup files
- Cannot access Django admin interface

### Superusers
- All regular user permissions
- Access to Django admin interface
- Can create and manage other users
- Full system administration capabilities

## Login Process

1. Navigate to the application URL
2. You will be redirected to the login page if not authenticated
3. Enter username and password
4. Upon successful login, you'll be redirected to the backup dashboard
5. Use the logout link in the navigation to sign out

## Troubleshooting

### Cannot Login
- Verify username and password are correct
- Check if account is active (not disabled)
- Contact system administrator if issues persist

### Forgot Password
- Contact system administrator to reset password
- Passwords can only be changed through admin interface or management commands

### Account Locked
- Contact system administrator to unlock account
- Check for multiple failed login attempts

## Contact Information

For user account issues or to request new accounts, contact your system administrator.

