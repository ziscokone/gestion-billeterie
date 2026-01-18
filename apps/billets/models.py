from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Billet(models.Model):
    """
    Modèle représentant un billet de transport.
    """
    STATUT_CHOICES = [
        ('reserve', 'Réservé'),
        ('paye', 'Payé'),
    ]

    numero = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Numéro du ticket"
    )
    voyage = models.ForeignKey(
        'voyages.Voyage',
        on_delete=models.CASCADE,
        related_name='billets',
        verbose_name="Voyage"
    )
    destination = models.ForeignKey(
        'destinations.Destination',
        on_delete=models.PROTECT,
        related_name='billets',
        verbose_name="Destination",
        null=True,
        blank=True
    )
    client_nom = models.CharField(max_length=200, verbose_name="Nom du client")
    client_telephone = models.CharField(max_length=20, verbose_name="Téléphone du client")
    numero_siege = models.PositiveIntegerField(verbose_name="Numéro de siège")
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name="Montant (FCFA)"
    )
    statut = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default='reserve',
        verbose_name="Statut"
    )
    guichetier = models.ForeignKey(
        'personnel.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='billets_vendus',
        verbose_name="Guichetier"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de paiement"
    )
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Billet"
        verbose_name_plural = "Billets"
        ordering = ['-date_creation']
        # Un siège ne peut être vendu qu'une fois par voyage
        unique_together = ['voyage', 'numero_siege']

    def __str__(self):
        return f"{self.numero} - {self.client_nom} (Siège {self.numero_siege})"

    def clean(self):
        """Validation du billet."""
        if self.voyage_id and self.numero_siege:
            # Vérifier si le siège est disponible
            if not self.pk:  # Nouveau billet
                if not self.voyage.siege_disponible(self.numero_siege):
                    raise ValidationError(
                        f"Le siège {self.numero_siege} n'est pas disponible pour ce voyage."
                    )

    def save(self, *args, **kwargs):
        # Générer le numéro de ticket si non défini
        if not self.numero:
            self.numero = self.voyage.gare.generer_numero_ticket()

        # Définir le montant depuis la destination si non défini
        if not self.montant and self.destination:
            self.montant = self.destination.montant
        elif not self.montant:
            # Si pas de destination spécifiée, le montant doit être fourni explicitement
            raise ValueError("Le montant doit être spécifié si aucune destination n'est fournie")

        super().save(*args, **kwargs)

    def payer(self):
        """Marque le billet comme payé."""
        if self.statut == 'paye':
            return False

        self.statut = 'paye'
        self.date_paiement = timezone.now()
        self.save(update_fields=['statut', 'date_paiement', 'date_modification'])
        return True

    @property
    def est_paye(self):
        return self.statut == 'paye'

    @property
    def est_reserve(self):
        return self.statut == 'reserve'

    def get_info_impression(self):
        """Retourne les informations pour l'impression du ticket."""
        gare = self.voyage.gare
        compagnie = gare.compagnie if gare else None

        return {
            'numero': self.numero,
            'numero_depart': self.voyage.numero_depart if hasattr(self.voyage, 'numero_depart') else 'N/A',
            'client_nom': self.client_nom,
            'numero_siege': self.numero_siege,
            'ligne': str(self.voyage.ligne),
            'destination': self.destination.ville_arrivee if self.destination else 'N/A',
            'date_depart': self.voyage.date_depart.strftime('%d/%m/%Y'),
            'heure_depart': self.voyage.heure_depart.strftime('%H:%M'),
            'periode': self.voyage.get_periode_display(),
            'montant': self.montant,
            # Informations de la gare
            'gare_nom': gare.nom if gare else '',
            'gare_adresse': gare.adresse if gare else '',
            'gare_telephone': gare.telephone if gare else '',
            # Informations de la compagnie
            'compagnie_nom': compagnie.nom if compagnie else '',
            'compagnie_logo': compagnie.logo.url if compagnie and compagnie.logo else '',
        }

    @classmethod
    def creer_billet(cls, voyage, client_nom, client_telephone, numero_siege, guichetier, destination=None, payer=True):
        """
        Crée un nouveau billet.

        Args:
            voyage: Instance du Voyage
            client_nom: Nom du client
            client_telephone: Téléphone du client
            numero_siege: Numéro du siège
            guichetier: Utilisateur qui crée le billet
            destination: Instance de la Destination choisie par le client
            payer: Si True, marque directement comme payé

        Returns:
            Instance du Billet créé
        """
        if not voyage.siege_disponible(numero_siege):
            raise ValidationError(f"Le siège {numero_siege} n'est pas disponible.")

        # Vérifier que la destination est fournie
        if not destination:
            raise ValidationError("Une destination doit être spécifiée pour créer un billet.")

        billet = cls(
            voyage=voyage,
            destination=destination,
            client_nom=client_nom,
            client_telephone=client_telephone,
            numero_siege=numero_siege,
            montant=destination.montant,
            guichetier=guichetier,
            statut='paye' if payer else 'reserve',
            date_paiement=timezone.now() if payer else None
        )
        billet.save()
        return billet

    @classmethod
    def creer_billets_plage(cls, voyage, client_nom, client_telephone, siege_debut, siege_fin, guichetier, destination, payer=True):
        """
        Crée plusieurs billets pour une plage de sièges.
        Ignore les sièges déjà pris.

        Args:
            voyage: Instance du Voyage
            client_nom: Nom du client
            client_telephone: Téléphone du client
            siege_debut: Premier siège de la plage
            siege_fin: Dernier siège de la plage
            guichetier: Utilisateur qui crée les billets
            destination: Instance de la Destination (obligatoire)
            payer: Si True, marque directement comme payé

        Returns:
            list: Liste des billets créés
        """
        if not destination:
            raise ValidationError("Une destination doit être spécifiée pour créer des billets.")

        billets_crees = []
        sieges_disponibles = voyage.get_sieges_disponibles()

        for numero_siege in range(siege_debut, siege_fin + 1):
            if numero_siege in sieges_disponibles:
                try:
                    billet = cls.creer_billet(
                        voyage=voyage,
                        client_nom=client_nom,
                        client_telephone=client_telephone,
                        numero_siege=numero_siege,
                        guichetier=guichetier,
                        destination=destination,
                        payer=payer
                    )
                    billets_crees.append(billet)
                except ValidationError:
                    # Siège déjà pris entre temps, on continue
                    continue

        return billets_crees
