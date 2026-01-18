from django.contrib import admin
from .models import ModeleVehicule, Vehicule


@admin.register(ModeleVehicule)
class ModeleVehiculeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'marque', 'capacite')
    list_filter = ('marque',)
    search_fields = ('nom', 'marque')
    ordering = ('marque', 'nom')

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'marque', 'capacite', 'description')
        }),
        ('Configuration des sièges', {
            'fields': ('disposition_sieges',),
            'classes': ('collapse',),
            'description': 'Configuration JSON de la disposition des sièges'
        }),
    )


@admin.register(Vehicule)
class VehiculeAdmin(admin.ModelAdmin):
    list_display = ('immatriculation', 'modele', 'annee_mise_service', 'actif')
    list_filter = ('modele', 'actif', 'annee_mise_service')
    search_fields = ('immatriculation', 'modele__nom')
    ordering = ('immatriculation',)

    fieldsets = (
        ('Informations générales', {
            'fields': ('immatriculation', 'modele', 'compagnie')
        }),
        ('Détails', {
            'fields': ('annee_mise_service', 'notes')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )
