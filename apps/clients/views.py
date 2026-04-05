from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.generic import DetailView, ListView

from .models import Client


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/liste.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        queryset = Client.objects.annotate(nb_billets=Count('billets'))
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(nom_complet__icontains=search) |
                Q(telephone__icontains=search)
            )
        return queryset.order_by('nom_complet')

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['nb_total'] = Client.objects.count()
        context['nb_ce_mois'] = Client.objects.filter(
            date_creation__month=timezone.now().month,
            date_creation__year=timezone.now().year
        ).count()
        context['nb_fideles'] = Client.objects.annotate(
            nb=Count('billets')
        ).filter(nb__gte=5).count()
        return context


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object

        billets = client.billets.select_related(
            'voyage', 'voyage__gare', 'voyage__ligne', 'destination'
        ).order_by('-date_creation')

        context['nb_voyages'] = billets.count()
        context['nb_payes'] = billets.filter(statut='paye').count()

        paginator = Paginator(billets, 10)
        page_number = self.request.GET.get('page', 1)
        context['billets'] = paginator.get_page(page_number)

        context['gares_frequentes'] = (
            billets.values('voyage__gare__nom')
            .annotate(nb=Count('id'))
            .order_by('-nb')[:5]
        )
        context['destinations_frequentes'] = (
            billets.filter(destination__isnull=False)
            .values('destination__ville_arrivee')
            .annotate(nb=Count('id'))
            .order_by('-nb')[:5]
        )
        return context


@login_required
def rechercher_client(request):
    telephone = request.GET.get('telephone', '').strip()
    if not telephone:
        return JsonResponse({'found': False})

    try:
        client = Client.objects.get(telephone=telephone)
        return JsonResponse({
            'found': True,
            'nom_complet': client.nom_complet,
            'telephone': client.telephone,
        })
    except Client.DoesNotExist:
        return JsonResponse({'found': False})


@login_required
def suggerer_clients(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 3:
        return JsonResponse({'clients': []})

    clients = Client.objects.filter(
        Q(telephone__icontains=q) | Q(nom_complet__icontains=q)
    ).order_by('telephone')[:6]

    return JsonResponse({
        'clients': [
            {'telephone': c.telephone, 'nom_complet': c.nom_complet}
            for c in clients
        ]
    })
