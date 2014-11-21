import os

from django.conf import global_settings


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = '2b2hfefg76_@rvvj4$(ql&me)zx3%%=rda3t+i*t!p+&frstym'

DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

ADMINS = (('Joan', 'joan.ardiaca@gmail.com'), )


# Application definition

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
"game.context_processors.player_processor", )

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

# TODO: static root

STATIC_URL = '/static/'

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

LOGIN_URL = '/login'


# Tests settings

SKIP_MAIL_TESTS = False


# Game settings

MAX_INVITES_PER_USER = 3

INVITE_CODE_LENGTH = 7

INVITE_MAIL_SENDER_ADDRESS = 'anonymous@localhost'

COMMANDS_PER_TURN = 5

MAX_BATTLE_ITERATIONS = 30

# TODO: dev vs production settings
# http://stackoverflow.com/questions/88259/how-do-you-configure-django-for-simple-development-and-deployment/88331
# http://stackoverflow.com/questions/4664724/distributing-django-projects-with-unique-secret-keys