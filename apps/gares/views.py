from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Gare
from .forms import GareForm


class GestionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux admins et chefs de gare."""

    def test_func(self):
        return self.request.user.has_global_access or self.request.user.is_chef_gare


class GareListView(GestionRequiredMixin, ListView):
    """Liste des gares."""
    model = Gare
    template_name = 'gares/gare_list.html'
    context_object_name = 'gares'

    def get_queryset(self):
        user = self.request.user
        if user.has_global_access:
            return Gare.objects.all()
        return Gare.objects.filter(pk=user.gare.pk) if user.gare else Gare.objects.none()


class GareCreateView(GestionRequiredMixin, CreateView):
    """Créer une nouvelle gare."""
    model = Gare
    form_class = GareForm
    template_name = 'gares/gare_form.html'
    success_url = reverse_lazy('gares:gare_list')

    def test_func(self):
        return self.request.user.has_global_access

    def form_valid(self, form):
        messages.success(self.request, 'Gare créée avec succès.')
        return super().form_valid(form)


class GareUpdateView(GestionRequiredMixin, UpdateView):
    """Modifier une gare."""
    model = Gare
    form_class = GareForm
    template_name = 'gares/gare_form.html'
    success_url = reverse_lazy('gares:gare_list')

    def test_func(self):
        user = self.request.user
        if user.has_global_access:
            return True
        if user.is_chef_gare and user.gare:
            return self.get_object().pk == user.gare.pk
        return False

    def form_valid(self, form):
        messages.success(self.request, 'Gare modifiée avec succès.')
        return super().form_valid(form)


class GareDeleteView(GestionRequiredMixin, DeleteView):
    """Supprimer une gare."""
    model = Gare
    template_name = 'gares/gare_confirm_delete.html'
    success_url = reverse_lazy('gares:gare_list')

    def test_func(self):
        return self.request.user.has_global_access

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Gare supprimée avec succès.')
        return super().delete(request, *args, **kwargs)
