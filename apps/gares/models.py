from django.db import models


class Gare(models.Model):
    """Modèle représentant une gare routière."""
    nom = models.CharField(max_length=200, verbose_name="Nom de la gare")
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code",
        help_text="Code unique pour la numérotation des tickets (ex: CKY, KND)"
    )
    ville = models.CharField(max_length=100, verbose_name="Ville")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    compagnie = models.ForeignKey(
        'compagnie.Compagnie',
        on_delete=models.CASCADE,
        related_name='gares',
        verbose_name="Compagnie"
    )
    active = models.BooleanField(default=True, verbose_name="Active")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # Compteur pour la numérotation des tickets
    dernier_numero_ticket = models.PositiveIntegerField(
        default=0,
        verbose_name="Dernier numéro de ticket"
    )
    mois_dernier_ticket = models.CharField(
        max_length=6,
        blank=True,
        default='',
        verbose_name="Mois du dernier ticket",
        help_text="Format YYYYMM pour la réinitialisation mensuelle"
    )

    class Meta:
        verbose_name = "Gare"
        verbose_name_plural = "Gares"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def get_chef_gare(self):
        """Retourne le chef de gare s'il existe."""
        return self.utilisateurs.filter(role='chef_gare', actif=True).first()

    def get_guichetiers(self):
        """Retourne tous les guichetiers actifs de cette gare."""
        return self.utilisateurs.filter(role='guichetier', actif=True)

    def generer_numero_ticket(self):
        """
        Génère un nouveau numéro de ticket unique pour cette gare.
        Format: {CODE}-{ANNEE}{MOIS}-{SEQUENCE:05d}
        Ex: CKY-202601-00001

        La séquence se réinitialise automatiquement chaque mois.
        Synchronise avec la BD pour éviter les doublons après migration.
        """
        from django.utils import timezone
        from apps.billets.models import Billet

        now = timezone.now()
        mois_actuel = now.strftime('%Y%m')
        prefixe = f"{self.code}-{mois_actuel}-"

        # Réinitialiser le compteur si on change de mois
        if self.mois_dernier_ticket != mois_actuel:
            self.dernier_numero_ticket = 0
            self.mois_dernier_ticket = mois_actuel

        # Vérifier le dernier numéro existant en BD pour ce mois
        # (sécurité après migration ou si compteur désynchronisé)
        dernier_billet = Billet.objects.filter(
            numero__startswith=prefixe
        ).order_by('-numero').first()

        if dernier_billet:
            try:
                # Extraire la séquence du numéro existant (ex: "00044" -> 44)
                sequence_existante = int(dernier_billet.numero.split('-')[-1])
                # S'assurer que notre compteur est au moins égal
                if self.dernier_numero_ticket < sequence_existante:
                    self.dernier_numero_ticket = sequence_existante
            except (ValueError, IndexError):
                pass

        self.dernier_numero_ticket += 1
        self.save(update_fields=['dernier_numero_ticket', 'mois_dernier_ticket'])

        return f"{prefixe}{self.dernier_numero_ticket:05d}"
