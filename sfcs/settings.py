"""
Django settings for sfcs project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-sae26)(slkk%77$mk#w5ffioy-%v)#h*k$3(+msaisbcudc89z'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['sfcsdev.xtractautomation.com', '127.0.0.1', 'localhost']

CORS_ALLOWED_ORIGINS = [
    'http://localhost:8080',
    'https://sfcs.xtractautomation.com',
    'https://sfcsdev.xtractautomation.com',
    'http://sfcsdev.xtractautomation.com',
    'http://sfcs.xtractautomation.com',
    'http://sfcs-checklist.s3-website.ap-south-1.amazonaws.com',
]
# Application definition
CSRF_TRUSTED_ORIGINS = [
    'https://sfcsdev.xtractautomation.com', 'http://sfcsdev.xtractautomation.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'corsheaders',
    'store_checklist',
    'accounts',
    'machine_maintenance',
    'pricing',
    'django_celery_results'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'sfcs.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sfcs.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'sfcs_checklist',
#         'USER': 'sfcs_checklist_admin',
#         'PASSWORD': 'Aic@1234',
#         'HOST': 'localhost',  # Or use your EC2 instance IP if MySQL is running on a different server
#         'PORT': '3306',       # MySQL default port
#     }
# }
REST_FRAMEWORK = {
    # 'DATETIME_FORMAT': '%d/%m/%y %H:%M',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'accounts.UserAccount'
ACCOUNT_SERIALIZER = 'accounts.serializers.UserCreateSerializer'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

DJOSER = {
    'LOGIN_FIELD': 'email',
    'USER_CREATE_PASSWORD_RETYPE': True,
    'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,
    'SEND_CONFIRMATION_EMAIL': True,
    'SET_PASSWORD_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
    #    'ACTIVATION_URL': 'activate/{uid}/{token}',
    #    'SEND_ACTIVATION_EMAIL': True,
    'SERIALIZERS': {
        'user_create': ACCOUNT_SERIALIZER,
        'user': ACCOUNT_SERIALIZER,
        'current_user': ACCOUNT_SERIALIZER,
        'user_delete': 'djoser.serializers.UserDeleteSerializer',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
AUTH_TOKEN_MODEL = 'authtoken.Token'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'

WEBSITE_URL = 'http://localhost:8000'

ZOHO_APIS_CLIENT_ID = '1000.KX15FQIOLVX0WOYAW1MD7EYQVJH12S'
ZOHO_APIS_CLIENT_SECRET = 'c0d9e4c91b89004aa5d161a6113bcade3ab9b5217b'
ZOHO_APIS_REDIRECT_URI = 'http://www.zoho.com/books'
ZOHO_APIS_REFRESH_TOKEN = '1000.68ce4af244943327bb7c9940e49f6fec.6c52c46dafbdc3c40df223bf10fa401c'
ZOHO_BOOKS_VEPL_ORGANIZATION_ID = '60006125627'

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
#         },
#     },
#     'handlers': {
#         'file': {
#             'level': 'INFO',
#             'class': 'logging.FileHandler',
#             'filename': BASE_DIR / 'error.log',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'celery': {
#             'handlers': ['file'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#     },
# }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtpout.secureserver.net'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'info@trainotel.com'
EMAIL_HOST_PASSWORD = 'Aic@34062173'
EMAIL_USE_SSL = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
