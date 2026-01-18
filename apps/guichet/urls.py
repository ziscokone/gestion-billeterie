from django.urls import path
from . import views

app_name = 'guichet'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('voyages/', views.VoyageListView.as_view(), name='voyage_list'),
    path('vente/<int:pk>/', views.VenteView.as_view(), name='vente'),
    path('reservations/', views.ReservationsListView.as_view(), name='reservations'),

    # API endpoints
    path('api/creer-billet/<int:voyage_id>/', views.creer_billet, name='creer_billet'),
    path('api/payer/<int:billet_id>/', views.payer_reservation, name='payer_reservation'),
    path('api/sieges/<int:voyage_id>/', views.get_sieges_status, name='sieges_status'),
    path('api/billet/<int:billet_id>/', views.get_billet_info, name='billet_info'),
]
