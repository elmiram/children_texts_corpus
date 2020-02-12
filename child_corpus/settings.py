#!/usr/bin/python
#  -- coding: utf8 --

"""
Django settings for Child Corpus project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import os
import json
from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Use a separate file for storing usernames and passwords
with open(os.path.join(BASE_DIR, '.secure.settings.json')) as secret:
    SECRET = json.loads(secret.read())

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = SECRET["DEBUG"]
TEMPLATE_DEBUG = DEBUG

# Identifies whether the code is running in prod
PROD = '/home/elmira' in BASE_DIR

# The URL of the corpus
PREFIX = '/children' if PROD else ''


if PROD:
    ALLOWED_HOSTS = ['.web-corpora.net']
else:
    ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Corpus',
    'annotator',
    'news',
    'audiofield',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.admindocs.middleware.XViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audiofield.middleware.threadlocals.ThreadLocals',
)

ROOT_URLCONF = 'child_corpus.urls'

WSGI_APPLICATION = 'child_corpus.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'TEST_CHARSET': 'UTF8',
        'HOST': '',
        'PORT': '3306',
    }
}

if PROD:
    DATABASES['default']['NAME'] = SECRET['PROD_DATABASES_NAME']
    DATABASES['default']['USER'] = SECRET['PROD_DATABASES_USER']
    DATABASES['default']['PASSWORD'] = SECRET['PROD_DATABASES_PASSWORD']
else:
    DATABASES['default']['NAME'] = SECRET['DEV_DATABASES_NAME']
    DATABASES['default']['USER'] = SECRET['DEV_DATABASES_USER']
    DATABASES['default']['PASSWORD'] = SECRET['DEV_DATABASES_PASSWORD']


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

LANGUAGES = (
    ('ru', _('Russian')),
    ('en', _('English')),
)

TIME_ZONE = 'UTC'
# todo set timezone

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

MEDIA_URL = PREFIX + '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

STATIC_URL = PREFIX + '/static/'

if PROD:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
else:
    STATICFILES_DIRS = (
        os.path.join(BASE_DIR, 'static/'),
    )


STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages'
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)


# Corpus related settings

if PROD:
    PATH_TO_MYSTEM = os.path.join(BASE_DIR, 'mystem')
else:
    PATH_TO_MYSTEM = SECRET["DEV_PATH_TO_MYSTEM"]

TEMPORARY_FILE_LOCATION = os.path.join(BASE_DIR, 'tempfiles')

# Frontend widget values
# 0-Keep original, 1-Mono, 2-Stereo
CHANNEL_TYPE_VALUE = 0

# 0-Keep original, 8000-8000Hz, 16000-16000Hz, 22050-22050Hz,
# 44100-44100Hz, 48000-48000Hz, 96000-96000Hz
FREQ_TYPE_VALUE = 8000

# 0-Keep original, 1-Convert to MP3, 2-Convert to WAV, 3-Convert to OGG
CONVERT_TYPE_VALUE = 0
