# settings.py

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', "django-insecure--f67ll=2-b2qolla9=1f8mtg@s=l8^y8aj=@ij-0f4)eg@%8(0")
SECRET_KEY = os.environ.get('SECRET_KEY', "django-insecure--f67ll=2-b2qolla9=1f8mtg@s=l8^y8aj=@ij-0f4)eg@%8(0")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Leer ALLOWED_HOSTS de variable de entorno
ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(',') if host.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# --- NUEVA SECCIÓN PARA CSRF_TRUSTED_ORIGINS ---
# Leer CSRF_TRUSTED_ORIGINS de variable de entorno
# Se espera una cadena separada por comas, como "https://ejemplo.com,https://otroejemplo.com"
CSRF_TRUSTED_ORIGINS_ENV = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if CSRF_TRUSTED_ORIGINS_ENV:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS_ENV.split(',') if origin.strip()]
else:
    # Valor predeterminado para desarrollo local si DEBUG es True
    # Puedes ajustar esto si necesitas otros orígenes en desarrollo
    if DEBUG:
        CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']
    else:
        CSRF_TRUSTED_ORIGINS = [] # En producción, es mejor que sea vacío si no se especifica


# Application definition

INSTALLED_APPS = [
    "app",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "eventhub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "eventhub.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Configuración de base de datos que puede usar variables de entorno
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Si hay DATABASE_URL (como en producción), se puede configurar para PostgreSQL
    # Por ahora mantenemos SQLite, pero se puede cambiar después
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
# Configuración de base de datos que puede usar variables de entorno
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Si hay DATABASE_URL (como en producción), se puede configurar para PostgreSQL
    # Por ahora mantenemos SQLite, pero se puede cambiar después
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


STATIC_URL = "/static/"

# Bootstrap 5
STATICFILES_DIRS = [BASE_DIR / "static"]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

AUTH_USER_MODEL = "app.User"
LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', "es-ar")
LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', "es-ar")

TIME_ZONE = os.environ.get('TIME_ZONE', "America/Argentina/Buenos_Aires")
TIME_ZONE = os.environ.get('TIME_ZONE', "America/Argentina/Buenos_Aires")

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = os.environ.get('LOGIN_REDIRECT_URL', "/events/")
LOGIN_REDIRECT_URL = os.environ.get('LOGIN_REDIRECT_URL', "/events/")

LOGIN_URL = os.environ.get('LOGIN_URL', "/accounts/login/")
LOGIN_URL = os.environ.get('LOGIN_URL', "/accounts/login/")

LOGOUT_REDIRECT_URL = os.environ.get('LOGOUT_REDIRECT_URL', "/accounts/login/")
LOGOUT_REDIRECT_URL = os.environ.get('LOGOUT_REDIRECT_URL', "/accounts/login/")