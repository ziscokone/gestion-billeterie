from django.db import models
import json


class ModeleVehicule(models.Model):
    """
    Modèle représentant un modèle/type de véhicule.
    Contient la configuration de la disposition des sièges.
    """
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du modèle",
        help_text="Ex: Yutong 70 places"
    )
    marque = models.CharField(max_length=100, verbose_name="Marque")
    capacite = models.PositiveIntegerField(verbose_name="Capacité (places vendables)")
    disposition_sieges = models.JSONField(
        verbose_name="Disposition des sièges",
        help_text="Configuration JSON de la disposition des sièges",
        default=dict
    )
    description = models.TextField(blank=True, verbose_name="Description")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modèle de véhicule"
        verbose_name_plural = "Modèles de véhicules"
        ordering = ['marque', 'nom']

    def __str__(self):
        return f"{self.marque} - {self.nom} ({self.capacite} places)"

    def get_sieges_vendables(self):
        """Retourne la liste des numéros de sièges vendables."""
        sieges = []
        disposition = self.disposition_sieges

        if not disposition:
            return list(range(1, self.capacite + 1))

        non_vendables = disposition.get('sieges_non_vendables', [])

        for rangee in disposition.get('rangees', []):
            for siege in rangee.get('sieges', []):
                if siege is not None and siege not in non_vendables:
                    sieges.append(siege)

        return sorted(sieges) if sieges else list(range(1, self.capacite + 1))

    def get_disposition_pour_affichage(self):
        """
        Retourne la disposition formatée pour l'affichage dans l'interface.
        """
        disposition = self.disposition_sieges
        if not disposition:
            # Disposition par défaut si non configurée
            return self._generer_disposition_defaut()

        non_vendables = disposition.get('sieges_non_vendables', [])
        rangees_formatees = []

        for rangee in disposition.get('rangees', []):
            sieges_rangee = []
            for siege in rangee.get('sieges', []):
                if siege is None:
                    sieges_rangee.append({'numero': None, 'type': 'couloir'})
                elif siege in non_vendables:
                    sieges_rangee.append({'numero': siege, 'type': 'non_vendable'})
                else:
                    sieges_rangee.append({'numero': siege, 'type': 'vendable'})
            rangees_formatees.append({
                'rang': rangee.get('rang'),
                'sieges': sieges_rangee
            })

        return {
            'colonnes': disposition.get('colonnes', 5),
            'rangees': rangees_formatees
        }

    def _generer_disposition_defaut(self):
        """Génère une disposition par défaut pour l'affichage."""
        colonnes = 5
        sieges_par_rangee = 4  # 2 + couloir + 2
        nb_rangees = (self.capacite + sieges_par_rangee - 1) // sieges_par_rangee

        rangees = []
        numero_siege = 1

        for i in range(nb_rangees):
            sieges = []
            for j in range(colonnes):
                if j == 2:  # Couloir au milieu
                    sieges.append({'numero': None, 'type': 'couloir'})
                elif numero_siege <= self.capacite:
                    sieges.append({'numero': numero_siege, 'type': 'vendable'})
                    numero_siege += 1
                else:
                    sieges.append({'numero': None, 'type': 'vide'})

            rangees.append({'rang': i + 1, 'sieges': sieges})

        return {'colonnes': colonnes, 'rangees': rangees}

    @staticmethod
    def generer_disposition_json(colonnes, nb_rangees, sieges_non_vendables=None):
        """
        Utilitaire pour générer une configuration JSON de disposition.

        Args:
            colonnes: nombre de colonnes (incluant le couloir)
            nb_rangees: nombre de rangées
            sieges_non_vendables: liste des numéros de sièges non vendables

        Returns:
            dict: Configuration JSON de la disposition
        """
        if sieges_non_vendables is None:
            sieges_non_vendables = []

        rangees = []
        numero_siege = 1
        position_couloir = colonnes // 2  # Couloir au milieu

        for i in range(nb_rangees):
            sieges = []
            for j in range(colonnes):
                if j == position_couloir:
                    sieges.append(None)  # Couloir
                else:
                    sieges.append(numero_siege)
                    numero_siege += 1

            rangees.append({
                'rang': i + 1,
                'sieges': sieges
            })

        return {
            'colonnes': colonnes,
            'rangees': rangees,
            'sieges_non_vendables': sieges_non_vendables
        }


class Vehicule(models.Model):
    """Modèle représentant un véhicule de la compagnie."""

    # Choix pour les champs
    TYPE_CARBURANT_CHOICES = [
        ('diesel', 'Diesel'),
        ('essence', 'Essence'),
        ('hybride', 'Hybride'),
        ('electrique', 'Électrique'),
        ('gnv', 'GNV (Gaz Naturel)'),
    ]

    TYPE_BOITE_CHOICES = [
        ('manuelle', 'Manuelle'),
        ('automatique', 'Automatique'),
    ]

    # Informations générales
    immatriculation = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Immatriculation"
    )
    modele = models.ForeignKey(
        ModeleVehicule,
        on_delete=models.PROTECT,
        related_name='vehicules',
        verbose_name="Modèle"
    )
    compagnie = models.ForeignKey(
        'compagnie.Compagnie',
        on_delete=models.CASCADE,
        related_name='vehicules',
        verbose_name="Compagnie"
    )
    annee_mise_service = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Année de mise en service"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    notes = models.TextField(blank=True, verbose_name="Notes")

    # Caractéristiques techniques
    numero_chassis = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro de châssis (VIN)"
    )
    annee_fabrication = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Année de fabrication"
    )
    date_mise_circulation = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de mise en circulation"
    )
    type_carburant = models.CharField(
        max_length=20,
        choices=TYPE_CARBURANT_CHOICES,
        blank=True,
        verbose_name="Type de carburant"
    )
    type_boite = models.CharField(
        max_length=20,
        choices=TYPE_BOITE_CHOICES,
        blank=True,
        verbose_name="Type de boîte"
    )

    # Documents & conformité légale
    compagnie_assurance = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Compagnie d'assurance"
    )
    date_expiration_assurance = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date d'expiration assurance"
    )
    date_expiration_visite_technique = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date d'expiration visite technique"
    )
    date_expiration_carte_grise = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date d'expiration carte grise"
    )
    date_expiration_licence_transport = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date d'expiration licence de transport"
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ['immatriculation']

    def __str__(self):
        return f"{self.immatriculation} ({self.modele.nom})"

    @property
    def capacite(self):
        """Retourne la capacité du véhicule."""
        return self.modele.capacite

    def get_sieges_vendables(self):
        """Retourne la liste des sièges vendables pour ce véhicule."""
        return self.modele.get_sieges_vendables()

    def get_cout_total_reparations(self):
        """Retourne le coût total des réparations du véhicule."""
        from django.db.models import Sum
        total = self.reparations.aggregate(total=Sum('montant'))['total']
        return total or 0

    def get_nombre_reparations(self):
        """Retourne le nombre total de réparations du véhicule."""
        return self.reparations.count()

    def get_derniere_reparation(self):
        """Retourne la dernière réparation effectuée."""
        return self.reparations.order_by('-date_reparation').first()

    def is_critique(self, seuil=2000000):
        """Vérifie si le véhicule a dépassé le seuil critique de coûts."""
        return self.get_cout_total_reparations() > seuil


class ReparationVehicule(models.Model):
    """Modèle représentant une réparation effectuée sur un véhicule."""

    TYPE_REPARATION_CHOICES = [
        ('mecanique', 'Mécanique'),
        ('carrosserie', 'Carrosserie'),
        ('electrique', 'Électrique'),
        ('pneumatiques', 'Pneumatiques'),
        ('revision', 'Révision'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
    ]

    vehicule = models.ForeignKey(
        Vehicule,
        on_delete=models.CASCADE,
        related_name='reparations',
        verbose_name="Véhicule"
    )
    date_reparation = models.DateField(verbose_name="Date de réparation")
    type_reparation = models.CharField(
        max_length=20,
        choices=TYPE_REPARATION_CHOICES,
        verbose_name="Type de réparation"
    )
    description = models.TextField(verbose_name="Description")
    garage_prestataire = models.CharField(
        max_length=200,
        verbose_name="Garage/Prestataire"
    )
    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Montant (FCFA)"
    )
    kilometrage = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Kilométrage"
    )
    pieces_remplacees = models.TextField(
        blank=True,
        verbose_name="Pièces remplacées"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='terminee',
        verbose_name="Statut"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Réparation de véhicule"
        verbose_name_plural = "Réparations de véhicules"
        ordering = ['-date_reparation']

    def __str__(self):
        return f"{self.vehicule.immatriculation} - {self.get_type_reparation_display()} - {self.date_reparation}"
