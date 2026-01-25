from django.urls import path
from . import views

app_name = 'comptabilite'

urlpatterns = [
    path('point-journalier/', views.PointJournalierView.as_view(), name='point_journalier'),
    path('rapport/', views.RapportPeriodeView.as_view(), name='rapport_periode'),
    path('rapport-par-gare/', views.RapportParGareView.as_view(), name='rapport_par_gare'),
    path('statistiques/', views.StatistiquesView.as_view(), name='statistiques'),
]
