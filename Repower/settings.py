import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = '2b2hfefg76_@rvvj4$(ql&me)zx3%%=rda3t+i*t!p+&frstym'

DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

ADMINS = (('Joan', 'joan.ardiaca@gmail.com'), )


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'account',
    'game'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'Repower.urls'

WSGI_APPLICATION = 'Repower.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

ATOMIC_REQUESTS = True  # TODO: doesn't seem to work


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

LOGIN_URL = '/login/'


# Tests settings

SKIP_MAIL_TESTS = False


# Game settings

MAX_INVITES_PER_USER = 3

INVITE_CODE_LENGTH = 7

INVITE_MAIL_SENDER_ADDRESS = 'anonymous@localhost'

COMMANDS_PER_TURN = 5