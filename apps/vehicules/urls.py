from django.urls import path
from . import views

app_name = 'vehicules'

urlpatterns = [
    # Modèles de véhicules
    path('modeles/', views.ModeleVehiculeListView.as_view(), name='modele_list'),
    path('modeles/ajouter/', views.ModeleVehiculeCreateView.as_view(), name='modele_create'),
    path('modeles/<int:pk>/modifier/', views.ModeleVehiculeUpdateView.as_view(), name='modele_update'),
    path('modeles/<int:pk>/supprimer/', views.ModeleVehiculeDeleteView.as_view(), name='modele_delete'),

    # Véhicules
    path('', views.VehiculeListView.as_view(), name='vehicule_list'),
    path('ajouter/', views.VehiculeCreateView.as_view(), name='vehicule_create'),
    path('<int:pk>/modifier/', views.VehiculeUpdateView.as_view(), name='vehicule_update'),
    path('<int:pk>/supprimer/', views.VehiculeDeleteView.as_view(), name='vehicule_delete'),
]
