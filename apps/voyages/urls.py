from django.urls import path
from . import views

app_name = 'voyages'

urlpatterns = [
    path('', views.VoyageListView.as_view(), name='voyage_list'),
    path('<int:pk>/', views.VoyageDetailView.as_view(), name='voyage_detail'),
    path('<int:pk>/bordereau/', views.VoyageBordereauView.as_view(), name='voyage_bordereau'),
    path('<int:pk>/liste-passagers/', views.VoyageListePassagersView.as_view(), name='voyage_liste_passagers'),
    path('<int:pk>/recap-destination/', views.VoyageRecapDestinationView.as_view(), name='voyage_recap_destination'),
    path('ajouter/', views.VoyageCreateView.as_view(), name='voyage_create'),
    path('<int:pk>/modifier/', views.VoyageUpdateView.as_view(), name='voyage_update'),
    path('<int:pk>/supprimer/', views.VoyageDeleteView.as_view(), name='voyage_delete'),
    # Routes AJAX pour la gestion des agents
    path('<int:pk>/agents/', views.get_voyage_agents, name='voyage_get_agents'),
    path('<int:pk>/agents/save/', views.save_voyage_agents, name='voyage_save_agents'),
    # Routes AJAX pour la gestion des dépenses
    path('<int:pk>/depenses/', views.get_voyage_depenses, name='voyage_get_depenses'),
    path('<int:pk>/depenses/add/', views.add_voyage_depenses, name='voyage_add_depenses'),
    # Routes AJAX pour la gestion de la recette bagages
    path('<int:pk>/bagages/', views.get_voyage_bagages, name='voyage_get_bagages'),
    path('<int:pk>/bagages/save/', views.save_voyage_bagages, name='voyage_save_bagages'),
    # Route AJAX pour terminer un voyage
    path('<int:pk>/terminer/', views.terminer_voyage, name='voyage_terminer'),
    # Routes AJAX pour la gestion du report de billets
    path('billets/<int:billet_id>/report/voyages/', views.get_voyages_report, name='get_voyages_report'),
    path('billets/<int:billet_id>/report/', views.reporter_billet, name='reporter_billet'),
    path('voyages/<int:voyage_id>/disposition/', views.get_disposition_voyage, name='get_disposition_voyage'),
    # Dashboard des reports
    path('dashboard/reports/', views.DashboardReportsView.as_view(), name='dashboard_reports'),
]
