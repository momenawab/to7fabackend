# Alternative database settings for development
# Copy this to settings.py if you want to use root user temporarily

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'to7fa_db',
        'USER': 'root',  # Using root user
        'PASSWORD': 'your_root_password',  # Replace with your actual root password
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Note: Using root user is not recommended for production
# Create a dedicated Django user for better security 