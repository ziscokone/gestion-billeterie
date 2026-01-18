from celery import shared_task
from django.utils import timezone


@shared_task
def creer_voyages_automatiques():
    """
    Tâche Celery pour créer automatiquement les voyages
    sur les 7 prochains jours à partir des programmes actifs.

    Cette tâche doit être exécutée quotidiennement (de préférence à minuit).
    """
    from apps.programmes.models import ProgrammeDepart

    total_crees = ProgrammeDepart.creer_tous_voyages(jours_avance=7)

    return f"{total_crees} voyage(s) créé(s) le {timezone.now().strftime('%d/%m/%Y %H:%M')}"


@shared_task
def nettoyer_voyages_passes():
    """
    Tâche pour marquer les voyages passés comme terminés.
    """
    from apps.voyages.models import Voyage
    from datetime import datetime

    now = timezone.now()
    today = now.date()

    # Marquer les voyages passés comme terminés
    voyages_a_terminer = Voyage.objects.filter(
        statut='programme',
        date_depart__lt=today
    )

    count = voyages_a_terminer.update(statut='termine')

    return f"{count} voyage(s) marqué(s) comme terminé(s)"
