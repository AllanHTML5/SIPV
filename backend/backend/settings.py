"""
Django settings for backend project.
"""

import os
from pathlib import Path

# ======================================
# BASE DIRECTORY
# ======================================
BASE_DIR = Path(__file__).resolve().parent.parent


# ======================================
# ENVIRONMENT VARIABLES
# ======================================
SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")


# ======================================
# APPLICATIONS
# ======================================
INSTALLED_APPS = [
    "widget_tweaks",
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",

    # SIPV Modules
    "maestros",
    "inventario.apps.InventarioConfig",
    "compras.apps.ComprasConfig",
    "ventas.apps.VentasConfig",
    "facturas",
    "caja",
    "sar",
    "auditoria",
    "common",
    "authapp",
]


# ======================================
# MIDDLEWARE
# ======================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ======================================
# URLS & WSGI
# ======================================
ROOT_URLCONF = "backend.urls"
WSGI_APPLICATION = "backend.wsgi.application"


# ======================================
# TEMPLATES
# ======================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.permisos.permisos_modulos",
            ],
        },
    },
]

UNFOLD = {}


# ======================================
# AUTH & LOGIN
# ======================================
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


# ======================================
# DATABASES
# ======================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "sipv"),
        "USER": os.getenv("DB_USER", "sipvuser"),
        "PASSWORD": os.getenv("DB_PASSWORD", "sipvpass"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}


# ======================================
# PASSWORD VALIDATION
# ======================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ======================================
# INTERNATIONALIZATION
# ======================================
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "es-hn")
TIME_ZONE = os.getenv("TIME_ZONE", "America/Tegucigalpa")

USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("es", "Español"),
    ("es-hn", "Honduras"),
    ("es-419", "Latinoamérica"),
    ("es-es", "España"),
    ("en", "English"),
]


# ======================================
# STATIC FILES
# ======================================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"


# ======================================
# DEFAULT PRIMARY KEY
# ======================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
