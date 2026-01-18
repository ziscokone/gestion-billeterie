from django.db import models


class Compagnie(models.Model):
    """
    Modèle représentant la compagnie de transport.
    Une seule instance de ce modèle devrait exister (singleton).
    """
    nom = models.CharField(max_length=200, verbose_name="Nom de la compagnie")
    logo = models.ImageField(
        upload_to='logos/',
        blank=True,
        null=True,
        verbose_name="Logo"
    )
    nom_pdg = models.CharField(max_length=200, verbose_name="Nom du PDG")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Compagnie"
        verbose_name_plural = "Compagnie"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        """Assure qu'il n'y a qu'une seule instance de Compagnie."""
        if not self.pk and Compagnie.objects.exists():
            existing = Compagnie.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Retourne l'instance unique de la compagnie ou None."""
        return cls.objects.first()
