"""
Django settings for infinity_fire_solutions project.

Generated by 'django-admin startproject' using Django 4.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-3&1voj3_&(tzrsww4^_!x!wht%0a2&x@jc@vw(y!23di798(6^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['54ad-49-249-18-102.ngrok-free.app','127.0.0.1','192.168.1.210', 'app-dev.infinityfireprevention.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authentication',
    'contact',
    'common_app',
    'todo',
    'cities_light',
    'rest_framework',
    'rest_framework.authtoken',
    'ckeditor',
    'customer_management',
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'infinity_fire_solutions.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                 # Other context processors
                'infinity_fire_solutions.context_processors.breadcrumbs', 
                'infinity_fire_solutions.context_processors.custom_menu'
            ],
            'libraries':  {
                'custom_tags': 'authentication.templatetags.custom_tags',
            }
        },
        
    },
]

WSGI_APPLICATION = 'infinity_fire_solutions.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'infinity_fire_solutions'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'root'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': '3306',
    }
}


# settings.py
REST_FRAMEWORK = {
    # ... other settings ...
    'EXCEPTION_HANDLER': 'infinity_fire_solutions.exceptions.custom_exception_handler'
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# AWS
STATIC_URL= 'https://ifp-static-dev.s3.eu-west-2.amazonaws.com/static/'
#STATIC_URL = '/static/'
#STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

#STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# if not DEBUG:
#     STATICFILES_DIRS = (
#         os.path.join(BASE_DIR, "static",),
#     )

#     STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# else:

#     STATICFILES_DIRS = (
#         os.path.join(BASE_DIR, "static"),
#         os.path.join(BASE_DIR, 'static'),
#     )

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# USER MODEL 
AUTH_USER_MODEL = 'authentication.User'
LOGIN_URL = '/auth/login/'

#AWS
AWS_BUCKET_NAME = 'ifp-assets-dev'
#supported file
SUPPORTED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'txt', 'pdf', 'doc', 'docx', 'csv', 'xls', 'xlsx', 'zip']


# Include data for English language translations
CITIES_LIGHT_TRANSLATION_LANGUAGES = ['en']

# Include data for the United Kingdom (UK)
CITIES_LIGHT_INCLUDE_COUNTRIES = ['UK']