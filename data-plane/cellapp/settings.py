from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "tenant-dbs"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "cell-platform-dev-not-for-production")
DEBUG = False
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "cellapp",
]

MIDDLEWARE = [
    "cellapp.middleware.TenantMiddleware",
]

ROOT_URLCONF = "cellapp.urls"
WSGI_APPLICATION = "cellapp.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DATA_DIR / "_default.sqlite3"),
    }
}

DATABASE_ROUTERS = ["cellapp.connections.TenantRouter"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
STATIC_URL = "/static/"
