"""
Django settings for Gestion Billetterie project.
"""

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-hd4+#uu!m996vv)m0^4@ki=k#=)$0**rw-dvspn0si&fuoz4_=')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Ajouter le domaine Render en production
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Sécurité
    'axes',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'two_factor',
    'auditlog',

    # Local apps
    'core',
    'apps.compagnie',
    'apps.gares',
    'apps.personnel',
    'apps.lignes',
    'apps.destinations',
    'apps.vehicules',
    'apps.programmes',
    'apps.voyages',
    'apps.billets',
    'apps.clients',
    'apps.guichet',
    'apps.comptabilite',

    # Cloudinary (doit être après les apps locales)
    'cloudinary_storage',
    'cloudinary',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'core.middleware.Force2FAMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.compagnie.context_processors.compagnie_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# Utilise PostgreSQL en production (via DATABASE_URL) ou SQLite en local
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Custom User Model
AUTH_USER_MODEL = 'personnel.Utilisateur'


# Password validation
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
LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Africa/Conakry'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise pour servir les fichiers statiques en production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary configuration (pour la production)
if os.environ.get('CLOUDINARY_CLOUD_NAME'):
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    }
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Login/Logout URLs
LOGIN_URL = 'two_factor:login'
LOGIN_REDIRECT_URL = 'guichet:dashboard'
LOGOUT_REDIRECT_URL = 'two_factor:login'
TWO_FACTOR_LOGIN_URL = 'two_factor:login'

# ─── Django Axes (protection brute force) ────────────────────────────────────
AXES_FAILURE_LIMIT = 5           # Bloquer après 5 tentatives échouées
AXES_COOLOFF_TIME = 1            # Débloquer après 1 heure
AXES_LOCKOUT_CALLABLE = None
AXES_RESET_ON_SUCCESS = True     # Réinitialiser le compteur après succès
AXES_ENABLE_ADMIN = True
AXES_VERBOSE = False

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ─── Sécurité des mots de passe ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Sessions sécurisées ─────────────────────────────────────────────────────
SESSION_COOKIE_AGE = 28800        # 8 heures
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# ─── Paramètres HTTPS (actifs en production uniquement) ─────────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

X_FRAME_OPTIONS = 'DENY'

# ─── Rôles qui doivent utiliser la 2FA ──────────────────────────────────────
ROLES_2FA_OBLIGATOIRE = ['super_admin', 'manager', 'chef_gare']


# ─── Jazzmin (Admin UI) ──────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    # Titre dans l'onglet navigateur
    "site_title": "Admin Billetterie",

    # Titre de la page d'en-tête
    "site_header": "Gestion Billetterie",

    # Titre du brand dans la sidebar
    "site_brand": "Billetterie",

    # Logo dans la sidebar (chemin relatif à STATIC_URL)
    "site_logo": None,

    # Logo sur la page de login
    "login_logo": None,

    # Icône du navigateur
    "site_icon": None,

    # Message de bienvenue sur la page de login
    "welcome_sign": "Administration — Accès restreint",

    # Texte du copyright en bas de page
    "copyright": "Gestion Billetterie CI",

    # Champ de recherche global : liste de modèles (app.Model)
    "search_model": ["personnel.Utilisateur", "billets.Billet", "voyages.Voyage"],

    # Afficher le champ de recherche en haut
    "user_avatar": None,

    # ── Barre supérieure ────────────────────────────────────────────────────
    "topmenu_links": [
        {"name": "Accueil Site", "url": "/", "new_window": False, "icon": "fas fa-home"},
        {"name": "Voyages", "url": "/voyages/", "new_window": False, "icon": "fas fa-bus"},
        {"model": "personnel.Utilisateur"},
    ],

    # ── Menu utilisateur (icône en haut à droite) ───────────────────────────
    "usermenu_links": [
        {"name": "Retour au site", "url": "/", "icon": "fas fa-home"},
    ],

    # ── Sidebar ─────────────────────────────────────────────────────────────
    "show_sidebar": True,
    "navigation_expanded": True,

    # Apps à masquer dans la sidebar
    "hide_apps": ["auth"],

    # Modèles à masquer dans la sidebar
    "hide_models": [],

    # Ordre des apps dans la sidebar
    "order_with_respect_to": [
        "compagnie",
        "gares",
        "personnel",
        "lignes",
        "destinations",
        "vehicules",
        "programmes",
        "voyages",
        "billets",
        "clients",
        "comptabilite",
        "axes",
        "auditlog",
        "django_otp",
        "otp_totp",
        "otp_static",
        "two_factor",
        "django_celery_beat",
    ],

    # Menu personnalisé (écrase l'ordre automatique si défini)
    "custom_links": {
        "billets": [{
            "name": "Rapport Billets",
            "url": "/comptabilite/",
            "icon": "fas fa-chart-bar",
        }],
    },

    # ── Icônes des modèles ───────────────────────────────────────────────────
    "icons": {
        # Icône par app (fallback)
        "compagnie": "fas fa-building",
        "gares": "fas fa-map-marker-alt",
        "personnel": "fas fa-users",
        "lignes": "fas fa-route",
        "destinations": "fas fa-map-signs",
        "vehicules": "fas fa-bus",
        "programmes": "fas fa-calendar-alt",
        "voyages": "fas fa-road",
        "billets": "fas fa-ticket-alt",
        "clients": "fas fa-user-friends",
        "comptabilite": "fas fa-coins",
        "axes": "fas fa-shield-alt",
        "auditlog": "fas fa-history",

        # Icône par modèle (app.Modele)
        "compagnie.Compagnie": "fas fa-building",
        "gares.Gare": "fas fa-map-marker-alt",
        "personnel.Utilisateur": "fas fa-user-shield",
        "personnel.Chauffeur": "fas fa-id-card",
        "personnel.Convoyeur": "fas fa-user-tie",
        "lignes.Ligne": "fas fa-route",
        "destinations.Destination": "fas fa-map-pin",
        "vehicules.Vehicule": "fas fa-bus-alt",
        "vehicules.ModeleVehicule": "fas fa-cogs",
        "vehicules.TypeReparation": "fas fa-tools",
        "vehicules.ReparationVehicule": "fas fa-wrench",
        "programmes.ProgrammeDepart": "fas fa-clock",
        "voyages.Voyage": "fas fa-road",
        "billets.Billet": "fas fa-ticket-alt",
        "billets.HistoriqueReport": "fas fa-history",
        "clients.Client": "fas fa-user-friends",
        "comptabilite.TypeDepense": "fas fa-tags",
        "comptabilite.Depense": "fas fa-money-bill-wave",
        "auth.Group": "fas fa-layer-group",
    },

    # Utiliser les icônes définies ci-dessus
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    # ── Comportement UI ─────────────────────────────────────────────────────
    "related_modal_active": True,       # Popups pour les FK
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": False,      # Pas de CDN Google (offline ok)
    "show_ui_builder": False,           # Masquer le builder en prod
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-teal",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
    "actions_sticky_top": True,
}
