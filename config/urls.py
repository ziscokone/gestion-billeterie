from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.guichet.urls')),
    path('personnel/', include('apps.personnel.urls')),
    path('comptabilite/', include('apps.comptabilite.urls')),
    path('gares/', include('apps.gares.urls')),
    path('lignes/', include('apps.lignes.urls')),
    path('destinations/', include('apps.destinations.urls')),
    path('vehicules/', include('apps.vehicules.urls')),
    path('programmes/', include('apps.programmes.urls')),
    path('voyages/', include('apps.voyages.urls')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
