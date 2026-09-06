"""
Django settings for the college_dbms project.

This project stores its *application* data (students, courses,
enrollments, history) in MongoDB via MongoEngine. Django's own
internal tables (admin/auth/sessions) still use SQLite, since Django
itself has no idea about MongoDB - MongoEngine is used independently
inside the dbms_app.
"""

import os
from pathlib import Path

import mongoengine

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-college-dbms-demo-key'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dbms_app',
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

ROOT_URLCONF = 'college_dbms.urls'

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

WSGI_APPLICATION = 'college_dbms.wsgi.application'

# Django's own bookkeeping tables only - NOT where our DBMS data lives.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'django_internal.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------
# MongoDB configuration (this is the real database for the project)
# ---------------------------------------------------------------------
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'college_dbms')
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')

mongoengine.connect(db=MONGO_DB_NAME, host=MONGO_URI, alias='default')
