from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta

from apps.billets.models import Billet
from apps.voyages.models import Voyage
from apps.gares.models import Gare
from apps.personnel.models import Utilisateur


class PointJournalierView(LoginRequiredMixin, TemplateView):
    """Point journalier des ventes."""
    template_name = 'comptabilite/point_journalier.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        date_str = self.request.GET.get('date')

        if date_str:
            try:
                from datetime import datetime
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                date = timezone.now().date()
        else:
            date = timezone.now().date()

        context['date_selectionnee'] = date

        # Construire le queryset de base
        billets_query = Billet.objects.filter(
            statut='paye',
            date_paiement__date=date
        )

        if not user.has_global_access:
            billets_query = billets_query.filter(voyage__gare=user.gare)

        # Stats globales
        stats = billets_query.aggregate(
            total_billets=Count('id'),
            total_montant=Sum('montant')
        )

        context['total_billets'] = stats['total_billets'] or 0
        context['total_montant'] = stats['total_montant'] or 0

        # Stats par guichetier
        if user.has_global_access or user.is_chef_gare:
            guichetiers_stats = billets_query.values(
                'guichetier__nom_complet',
                'guichetier__id'
            ).annotate(
                nb_billets=Count('id'),
                montant=Sum('montant')
            ).order_by('-montant')

            context['guichetiers_stats'] = guichetiers_stats

        # Stats par gare (pour admin global)
        if user.has_global_access:
            gares_stats = billets_query.values(
                'voyage__gare__nom',
                'voyage__gare__id'
            ).annotate(
                nb_billets=Count('id'),
                montant=Sum('montant')
            ).order_by('-montant')

            context['gares_stats'] = gares_stats

        # Liste des derniers billets
        context['derniers_billets'] = billets_query.order_by('-date_paiement')[:20]

        return context


class RapportPeriodeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Rapport sur une période donnée (admin/chef de gare/guichetier)."""
    template_name = 'comptabilite/rapport_periode.html'

    def test_func(self):
        user = self.request.user
        return user.has_global_access or user.is_chef_gare or user.is_guichetier

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Dates de la période
        date_debut_str = self.request.GET.get('date_debut')
        date_fin_str = self.request.GET.get('date_fin')

        today = timezone.now().date()

        if date_debut_str:
            try:
                from datetime import datetime
                date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            except ValueError:
                date_debut = today - timedelta(days=7)
        else:
            date_debut = today - timedelta(days=7)

        if date_fin_str:
            try:
                from datetime import datetime
                date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()
            except ValueError:
                date_fin = today
        else:
            date_fin = today

        context['date_debut'] = date_debut
        context['date_fin'] = date_fin

        # Queryset de base
        billets_query = Billet.objects.filter(
            statut='paye',
            date_paiement__date__gte=date_debut,
            date_paiement__date__lte=date_fin
        )

        if not user.has_global_access:
            billets_query = billets_query.filter(voyage__gare=user.gare)

        # Stats globales
        stats = billets_query.aggregate(
            total_billets=Count('id'),
            total_montant=Sum('montant')
        )

        context['total_billets'] = stats['total_billets'] or 0
        context['total_montant'] = stats['total_montant'] or 0

        # Stats par jour
        stats_par_jour = billets_query.values(
            'date_paiement__date'
        ).annotate(
            nb_billets=Count('id'),
            montant=Sum('montant')
        ).order_by('date_paiement__date')

        context['stats_par_jour'] = stats_par_jour

        # Stats par ligne
        stats_par_ligne = billets_query.values(
            'voyage__ligne__nom'
        ).annotate(
            nb_billets=Count('id'),
            montant=Sum('montant')
        ).order_by('-montant')

        context['stats_par_ligne'] = stats_par_ligne

        # Stats par guichetier
        stats_par_guichetier = billets_query.values(
            'guichetier__nom_complet'
        ).annotate(
            nb_billets=Count('id'),
            montant=Sum('montant')
        ).order_by('-montant')

        context['stats_par_guichetier'] = stats_par_guichetier

        # Gares disponibles pour filtrage (admin global)
        if user.has_global_access:
            context['gares'] = Gare.objects.filter(active=True)

        return context


class StatistiquesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Statistiques globales (PDG/Super Admin)."""
    template_name = 'comptabilite/statistiques.html'

    def test_func(self):
        return self.request.user.has_global_access

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Stats du jour
        billets_jour = Billet.objects.filter(
            statut='paye',
            date_paiement__date=today
        )
        context['jour_billets'] = billets_jour.count()
        context['jour_montant'] = billets_jour.aggregate(Sum('montant'))['montant__sum'] or 0

        # Stats de la semaine
        debut_semaine = today - timedelta(days=today.weekday())
        billets_semaine = Billet.objects.filter(
            statut='paye',
            date_paiement__date__gte=debut_semaine,
            date_paiement__date__lte=today
        )
        context['semaine_billets'] = billets_semaine.count()
        context['semaine_montant'] = billets_semaine.aggregate(Sum('montant'))['montant__sum'] or 0

        # Stats du mois
        debut_mois = today.replace(day=1)
        billets_mois = Billet.objects.filter(
            statut='paye',
            date_paiement__date__gte=debut_mois,
            date_paiement__date__lte=today
        )
        context['mois_billets'] = billets_mois.count()
        context['mois_montant'] = billets_mois.aggregate(Sum('montant'))['montant__sum'] or 0

        # Top 5 gares
        context['top_gares'] = Billet.objects.filter(
            statut='paye',
            date_paiement__date__gte=debut_mois
        ).values(
            'voyage__gare__nom'
        ).annotate(
            total=Sum('montant')
        ).order_by('-total')[:5]

        # Top 5 lignes
        context['top_lignes'] = Billet.objects.filter(
            statut='paye',
            date_paiement__date__gte=debut_mois
        ).values(
            'voyage__ligne__nom'
        ).annotate(
            total=Sum('montant')
        ).order_by('-total')[:5]

        # Réservations en attente
        context['reservations_attente'] = Billet.objects.filter(
            statut='reserve',
            voyage__date_depart__gte=today
        ).count()

        # Voyages du jour
        context['voyages_jour'] = Voyage.objects.filter(date_depart=today).count()

        return context
