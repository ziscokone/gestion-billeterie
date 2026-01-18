from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from core.mixins import GestionRequiredMixin
from .models import Destination
from .forms import DestinationForm


class DestinationListView(GestionRequiredMixin, ListView):
    """Liste des destinations."""
    model = Destination
    template_name = 'destinations/destination_list.html'
    context_object_name = 'destinations'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtrer par gare pour les chefs de gare et guichetiers
        if not user.has_global_access and user.gare:
            queryset = queryset.filter(gare=user.gare)

        # Recherche
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(ville_arrivee__icontains=search) |
                Q(ligne__nom__icontains=search)
            )

        return queryset.select_related('ligne', 'gare').order_by('ligne__nom', 'ville_arrivee')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class DestinationCreateView(GestionRequiredMixin, CreateView):
    """Créer une nouvelle destination."""
    model = Destination
    form_class = DestinationForm
    template_name = 'destinations/destination_form.html'
    success_url = reverse_lazy('destinations:destination_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Destination créée avec succès.')
        return super().form_valid(form)


class DestinationUpdateView(GestionRequiredMixin, UpdateView):
    """Modifier une destination."""
    model = Destination
    form_class = DestinationForm
    template_name = 'destinations/destination_form.html'
    success_url = reverse_lazy('destinations:destination_list')

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtrer par gare pour les chefs de gare et guichetiers
        if not user.has_global_access and user.gare:
            queryset = queryset.filter(gare=user.gare)

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Destination modifiée avec succès.')
        return super().form_valid(form)


class DestinationDeleteView(GestionRequiredMixin, DeleteView):
    """Supprimer une destination."""
    model = Destination
    template_name = 'destinations/destination_confirm_delete.html'
    success_url = reverse_lazy('destinations:destination_list')

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtrer par gare pour les chefs de gare et guichetiers
        if not user.has_global_access and user.gare:
            queryset = queryset.filter(gare=user.gare)

        return queryset

    def form_valid(self, form):
        messages.success(self.request, 'Destination supprimée avec succès.')
        return super().form_valid(form)
