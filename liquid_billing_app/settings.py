# liquid_billing_app/settings.py

from pathlib import Path
import os # Asegúrate de que 'os' esté importado si usas os.path.join o os.environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'tu_clave_secreta_por_defecto_para_desarrollo') # Ejemplo: Cargar de variable de entorno

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True' # Ejemplo: Cargar de variable de entorno, por defecto True para desarrollo

ALLOWED_HOSTS = ['jules-ikyj.onrender.com', 'localhost', '127.0.0.1'] # Deberás configurar esto para producción, ej: ['tu_dominio.com']
# Si usas DigitalOcean App Platform, ellos suelen manejar esto o te dan una variable para poner aquí.


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', # Necesario para la gestión de archivos estáticos
    'invoicing', # Tu aplicación
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

ROOT_URLCONF = 'liquid_billing_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Añade BASE_DIR / 'templates' si tienes una carpeta de plantillas a nivel de proyecto
        'DIRS': [BASE_DIR / 'invoicing/templates', BASE_DIR / 'templates'], 
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

WSGI_APPLICATION = 'liquid_billing_app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# Para producción (ej. DigitalOcean App Platform con PostgreSQL), esto se configuraría
# diferente, a menudo usando dj_database_url y una variable de entorno DATABASE_URL.
# Por ejemplo:
# import dj_database_url
# DATABASE_URL = os.environ.get('DATABASE_URL')
# if DATABASE_URL:
#     DATABASES['default'] = dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=os.environ.get('DB_SSL_REQUIRE', 'False') == 'True')


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'es-es' # Cambiado a español

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True # Cambiado en Django 4.0 a USE_TZ

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Directorio donde collectstatic copiará todos los archivos estáticos para producción.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Directorios adicionales para buscar archivos estáticos (opcional).
# STATICFILES_DIRS = [
#     BASE_DIR / 'static', # Si tienes una carpeta 'static' en la raíz de tu proyecto (fuera de cualquier app)
# ]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/app/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_URL = '/accounts/login/'
