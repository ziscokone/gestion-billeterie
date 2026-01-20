from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages

from apps.voyages.models import Voyage
from apps.billets.models import Billet
from apps.destinations.models import Destination


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal du guichetier."""
    template_name = 'guichet/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        # Filtrer les voyages selon les droits de l'utilisateur
        if user.has_global_access:
            voyages_today = Voyage.objects.filter(date_depart=today)
            billets_today = Billet.objects.filter(
                date_creation__date=today,
                statut='paye'
            )
        else:
            voyages_today = Voyage.objects.filter(
                date_depart=today,
                gare=user.gare
            )
            billets_today = Billet.objects.filter(
                date_creation__date=today,
                guichetier=user,
                statut='paye'
            )

        context['voyages_today'] = voyages_today.count()
        context['billets_vendus_today'] = billets_today.count()
        context['montant_today'] = sum(b.montant for b in billets_today)
        context['reservations_en_attente'] = Billet.objects.filter(
            statut='reserve',
            voyage__date_depart__gte=today
        ).count() if user.has_global_access else Billet.objects.filter(
            statut='reserve',
            voyage__gare=user.gare,
            voyage__date_depart__gte=today
        ).count()

        # Prochains voyages (filtrés par gare)
        prochains_voyages = Voyage.objects.filter(
            date_depart__gte=today,
            statut__in=['programme', 'en_cours']
        )
        if not user.has_global_access and user.gare:
            prochains_voyages = prochains_voyages.filter(gare=user.gare)
        context['prochains_voyages'] = prochains_voyages.order_by('date_depart', 'heure_depart')[:5]

        return context


class VoyageListView(LoginRequiredMixin, ListView):
    """Liste des voyages disponibles."""
    model = Voyage
    template_name = 'guichet/voyage_list.html'
    context_object_name = 'voyages'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()

        # Filtre de statut
        statut_filter = self.request.GET.get('statut', 'actifs')

        # Définir les statuts à afficher selon le filtre
        if statut_filter == 'termine':
            statuts = ['termine']
        elif statut_filter == 'tous':
            statuts = ['programme', 'en_cours', 'termine']
        else:  # 'actifs' par défaut
            statuts = ['programme', 'en_cours']

        # Vérifier si une date spécifique est demandée
        date_filter = self.request.GET.get('date')

        if date_filter:
            # Si une date est sélectionnée, afficher les voyages de cette date
            queryset = Voyage.objects.filter(
                date_depart=date_filter,
                statut__in=statuts
            )
        else:
            # Sinon, afficher les voyages à partir d'aujourd'hui
            queryset = Voyage.objects.filter(
                date_depart__gte=today,
                statut__in=statuts
            )

        if not user.has_global_access:
            queryset = queryset.filter(gare=user.gare)

        # Autres filtres
        ligne_filter = self.request.GET.get('ligne')
        periode_filter = self.request.GET.get('periode')

        if ligne_filter:
            queryset = queryset.filter(ligne_id=ligne_filter)
        if periode_filter:
            queryset = queryset.filter(periode=periode_filter)

        return queryset.order_by('date_depart', 'heure_depart')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Lignes disponibles pour le filtre
        if user.has_global_access:
            from apps.lignes.models import Ligne
            context['lignes'] = Ligne.objects.filter(active=True)
        else:
            context['lignes'] = user.gare.destinations.values_list(
                'ligne', flat=True
            ).distinct() if user.gare else []

        # Ajouter le filtre de statut actuel au contexte
        context['statut_filter'] = self.request.GET.get('statut', 'actifs')

        return context


class VenteView(LoginRequiredMixin, DetailView):
    """Interface de vente de billets pour un voyage."""
    model = Voyage
    template_name = 'guichet/vente.html'
    context_object_name = 'voyage'

    def get_queryset(self):
        """Filtrer les voyages par gare pour les utilisateurs non-global."""
        queryset = super().get_queryset()
        user = self.request.user
        if not user.has_global_access and user.gare:
            queryset = queryset.filter(gare=user.gare)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voyage = self.object

        context['disposition_sieges'] = voyage.get_disposition_sieges_avec_statut()
        context['sieges_disponibles'] = voyage.get_sieges_disponibles()
        context['nb_disponibles'] = len(context['sieges_disponibles'])
        context['reservations'] = voyage.billets.filter(statut='reserve')

        # Récupérer les destinations disponibles pour cette ligne
        context['destinations'] = Destination.objects.filter(
            ligne=voyage.ligne,
            gare=voyage.gare,
            active=True
        ).order_by('montant')

        return context


@login_required
def creer_billet(request, voyage_id):
    """Crée un ou plusieurs billets."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

    voyage = get_object_or_404(Voyage, pk=voyage_id)
    user = request.user

    # Vérifier les droits d'accès
    if not user.has_global_access and voyage.gare != user.gare:
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})

    client_nom = request.POST.get('client_nom', '').strip()
    client_telephone = request.POST.get('client_telephone', '').strip()
    destination_id = request.POST.get('destination_id')
    mode_vente = request.POST.get('mode_vente', 'unitaire')
    payer = request.POST.get('payer', 'true') == 'true'
    moyen_paiement = request.POST.get('moyen_paiement', 'cash')

    if not client_nom or not client_telephone:
        return JsonResponse({
            'success': False,
            'error': 'Le nom et le téléphone du client sont obligatoires'
        })

    # Récupérer la destination (obligatoire)
    if not destination_id:
        return JsonResponse({
            'success': False,
            'error': 'La destination est obligatoire'
        })

    try:
        destination = Destination.objects.get(pk=destination_id, ligne=voyage.ligne)
    except Destination.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Destination invalide'
        })

    billets_crees = []

    try:
        if mode_vente == 'unitaire':
            numero_siege = int(request.POST.get('numero_siege', 0))
            if not numero_siege:
                return JsonResponse({
                    'success': False,
                    'error': 'Numéro de siège non spécifié'
                })

            billet = Billet.creer_billet(
                voyage=voyage,
                client_nom=client_nom,
                client_telephone=client_telephone,
                numero_siege=numero_siege,
                guichetier=user,
                destination=destination,
                payer=payer,
                moyen_paiement=moyen_paiement
            )
            billets_crees.append(billet)

        elif mode_vente == 'plage':
            siege_debut = int(request.POST.get('siege_debut', 0))
            siege_fin = int(request.POST.get('siege_fin', 0))

            if not siege_debut or not siege_fin:
                return JsonResponse({
                    'success': False,
                    'error': 'Plage de sièges non spécifiée'
                })

            if siege_debut > siege_fin:
                siege_debut, siege_fin = siege_fin, siege_debut

            billets_crees = Billet.creer_billets_plage(
                voyage=voyage,
                client_nom=client_nom,
                client_telephone=client_telephone,
                siege_debut=siege_debut,
                siege_fin=siege_fin,
                guichetier=user,
                destination=destination,
                payer=payer,
                moyen_paiement=moyen_paiement
            )

        if not billets_crees:
            return JsonResponse({
                'success': False,
                'error': 'Aucun billet créé. Les sièges sont peut-être déjà pris.'
            })

        # Préparer les données pour l'impression
        billets_data = [billet.get_info_impression() for billet in billets_crees]

        return JsonResponse({
            'success': True,
            'message': f'{len(billets_crees)} billet(s) créé(s)',
            'billets': billets_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def payer_reservation(request, billet_id):
    """Convertit une réservation en paiement."""
    billet = get_object_or_404(Billet, pk=billet_id)
    user = request.user

    # Vérifier les droits d'accès
    if not user.has_global_access and billet.voyage.gare != user.gare:
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})

    if billet.statut == 'paye':
        return JsonResponse({
            'success': False,
            'error': 'Ce billet est déjà payé'
        })

    # Récupérer le moyen de paiement (par défaut cash)
    moyen_paiement = request.POST.get('moyen_paiement', 'cash')
    billet.payer(moyen_paiement=moyen_paiement)

    return JsonResponse({
        'success': True,
        'message': 'Paiement enregistré',
        'billet': billet.get_info_impression()
    })


@login_required
def get_sieges_status(request, voyage_id):
    """Retourne le statut actuel des sièges (pour mise à jour AJAX)."""
    voyage = get_object_or_404(Voyage, pk=voyage_id)

    disposition = voyage.get_disposition_sieges_avec_statut()

    return JsonResponse({
        'success': True,
        'disposition': disposition,
        'stats': {
            'disponibles': voyage.get_nb_places_disponibles(),
            'reserves': voyage.get_nb_places_reservees(),
            'payes': voyage.get_nb_places_vendues()
        }
    })


class ReservationsListView(LoginRequiredMixin, ListView):
    """Liste des réservations en attente de paiement."""
    model = Billet
    template_name = 'guichet/reservations.html'
    context_object_name = 'reservations'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()

        queryset = Billet.objects.filter(
            statut='reserve',
            voyage__date_depart__gte=today
        )

        if not user.has_global_access:
            queryset = queryset.filter(voyage__gare=user.gare)

        # Recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(client_nom__icontains=search) |
                Q(client_telephone__icontains=search) |
                Q(numero__icontains=search)
            )

        return queryset.order_by('voyage__date_depart', 'voyage__heure_depart')


@login_required
def get_billet_info(request, billet_id):
    """Retourne les informations d'un billet pour réimpression."""
    billet = get_object_or_404(Billet, pk=billet_id)
    user = request.user

    # Vérifier les droits d'accès
    if not user.has_global_access and billet.voyage.gare != user.gare:
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})

    return JsonResponse({
        'success': True,
        'billet': billet.get_info_impression()
    })
