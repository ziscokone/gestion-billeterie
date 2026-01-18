from django.contrib import admin
from .models import Gare


@admin.register(Gare)
class GareAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'ville', 'telephone', 'active')
    list_filter = ('active', 'ville')
    search_fields = ('nom', 'code', 'ville')
    ordering = ('nom',)

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'code', 'ville', 'compagnie')
        }),
        ('Contact', {
            'fields': ('adresse', 'telephone')
        }),
        ('Statut', {
            'fields': ('active',)
        }),
    )
