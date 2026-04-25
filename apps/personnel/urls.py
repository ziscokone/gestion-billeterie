from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from . import views

app_name = 'personnel'

urlpatterns = [
    # Redirection login vers two_factor (rétrocompatibilité des liens existants)
    path('login/', RedirectView.as_view(pattern_name='two_factor:login', permanent=False), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Utilisateurs
    path('utilisateurs/', views.UtilisateurListView.as_view(), name='utilisateur_list'),
    path('utilisateurs/ajouter/', views.UtilisateurCreateView.as_view(), name='utilisateur_create'),
    path('utilisateurs/<int:pk>/modifier/', views.UtilisateurUpdateView.as_view(), name='utilisateur_update'),
    path('utilisateurs/<int:pk>/supprimer/', views.UtilisateurDeleteView.as_view(), name='utilisateur_delete'),
    path('utilisateurs/<int:pk>/reset-2fa/', views.Reset2FAView.as_view(), name='reset_2fa'),

    # Chauffeurs
    path('chauffeurs/', views.ChauffeurListView.as_view(), name='chauffeur_list'),
    path('chauffeurs/ajouter/', views.ChauffeurCreateView.as_view(), name='chauffeur_create'),
    path('chauffeurs/<int:pk>/', views.ChauffeurDetailView.as_view(), name='chauffeur_detail'),
    path('chauffeurs/<int:pk>/modifier/', views.ChauffeurUpdateView.as_view(), name='chauffeur_update'),
    path('chauffeurs/<int:pk>/supprimer/', views.ChauffeurDeleteView.as_view(), name='chauffeur_delete'),

    # Convoyeurs
    path('convoyeurs/', views.ConvoyeurListView.as_view(), name='convoyeur_list'),
    path('convoyeurs/ajouter/', views.ConvoyeurCreateView.as_view(), name='convoyeur_create'),
    path('convoyeurs/<int:pk>/modifier/', views.ConvoyeurUpdateView.as_view(), name='convoyeur_update'),
    path('convoyeurs/<int:pk>/supprimer/', views.ConvoyeurDeleteView.as_view(), name='convoyeur_delete'),
]
