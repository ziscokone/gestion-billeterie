from django.urls import path

from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.ClientListView.as_view(), name='client_list'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('api/rechercher/', views.rechercher_client, name='rechercher_client'),
    path('api/suggerer/', views.suggerer_clients, name='suggerer_clients'),
]
