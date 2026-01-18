from django.urls import path
from . import views

app_name = 'destinations'

urlpatterns = [
    path('', views.DestinationListView.as_view(), name='destination_list'),
    path('ajouter/', views.DestinationCreateView.as_view(), name='destination_create'),
    path('<int:pk>/modifier/', views.DestinationUpdateView.as_view(), name='destination_update'),
    path('<int:pk>/supprimer/', views.DestinationDeleteView.as_view(), name='destination_delete'),
]
