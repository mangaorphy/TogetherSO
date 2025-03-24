from .settings import *
from dotenv import load_dotenv

DEBUG = False
ALLOWED_HOSTS = ['*']

# Use WhiteNoise for serving static files
INSTALLED_APPS += ['whitenoise.runserver_nostatic']
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware',)  # Insert after SecurityMiddleware

STATIC_ROOT = BASE_DIR / 'productionfiles'

STATIC_URL = 'static/'

# Database Configuration (e.g., PostgreSQL or MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'togetherso',
        'USER': 'togetherso_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

load_dotenv()  # Load environment variables from .env file
SECRET_KEY = os.getenv('SECRET_KEY')

# Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'  # SendGrid API key as username
EMAIL_HOST_PASSWORD = os.getenv('SENDGRID_API_KEY')  # SendGrid API key as password

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True