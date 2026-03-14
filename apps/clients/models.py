from django.db import models


class Client(models.Model):
    telephone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Téléphone"
    )
    nom_complet = models.CharField(
        max_length=200,
        verbose_name="Nom complet"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom_complet']

    def __str__(self):
        return f"{self.nom_complet} ({self.telephone})"

    @property
    def nombre_voyages(self):
        return self.billets.filter(statut__in=['paye', 'reserve', 'reporte']).count()
