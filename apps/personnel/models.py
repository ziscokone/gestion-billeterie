from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UtilisateurManager(BaseUserManager):
    """Manager personnalisé pour le modèle Utilisateur."""

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Le nom d'utilisateur est obligatoire")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)


class Utilisateur(AbstractUser):
    """
    Modèle utilisateur personnalisé pour la gestion des rôles.
    """
    ROLE_CHOICES = [
        ('pdg', 'PDG'),
        ('super_admin', 'Super Administrateur'),
        ('manager', 'Manager'),
        ('chef_gare', 'Chef de Gare'),
        ('guichetier', 'Guichetier'),
    ]

    nom_complet = models.CharField(max_length=200, verbose_name="Nom complet")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='guichetier',
        verbose_name="Rôle"
    )
    gare = models.ForeignKey(
        'gares.Gare',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='utilisateurs',
        verbose_name="Gare"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = UtilisateurManager()

    # Pas besoin d'email pour la connexion
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['nom_complet']

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['nom_complet']

    def __str__(self):
        return f"{self.nom_complet} ({self.get_role_display()})"

    @property
    def is_pdg(self):
        return self.role == 'pdg'

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_chef_gare(self):
        return self.role == 'chef_gare'

    @property
    def is_guichetier(self):
        return self.role == 'guichetier'

    @property
    def has_global_access(self):
        """Vérifie si l'utilisateur a accès à toutes les gares."""
        return self.role in ['pdg', 'super_admin', 'manager']

    def get_gares_accessibles(self):
        """Retourne les gares accessibles par l'utilisateur."""
        from apps.gares.models import Gare
        if self.has_global_access:
            return Gare.objects.filter(active=True)
        elif self.gare:
            return Gare.objects.filter(pk=self.gare.pk)
        return Gare.objects.none()


class Chauffeur(models.Model):
    """Modèle représentant un chauffeur de la compagnie."""

    SITUATION_MATRIMONIALE_CHOICES = [
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié(e)'),
        ('divorce', 'Divorcé(e)'),
        ('veuf', 'Veuf/Veuve'),
    ]

    # Informations générales
    nom_complet = models.CharField(max_length=200, verbose_name="Nom complet")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    numero_permis = models.CharField(max_length=50, verbose_name="Numéro de permis")

    # Identité
    numero_cni = models.CharField(max_length=50, blank=True, verbose_name="Numéro CNI")
    situation_matrimoniale = models.CharField(
        max_length=20,
        choices=SITUATION_MATRIMONIALE_CHOICES,
        blank=True,
        verbose_name="Situation matrimoniale"
    )
    nombre_enfants = models.PositiveIntegerField(default=0, verbose_name="Nombre d'enfants en charge")

    # Coordonnées
    telephone_2 = models.CharField(max_length=20, blank=True, verbose_name="Deuxième téléphone")
    lieu_habitation = models.CharField(max_length=200, blank=True, verbose_name="Lieu d'habitation")

    # Contact d'urgence
    personne_urgence = models.CharField(max_length=200, blank=True, verbose_name="Personne à contacter en cas d'urgence")
    telephone_urgence = models.CharField(max_length=20, blank=True, verbose_name="Téléphone personne d'urgence")

    # Informations professionnelles
    date_embauche = models.DateField(null=True, blank=True, verbose_name="Date d'embauche")
    salaire = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name="Salaire")
    cv = models.FileField(upload_to='chauffeurs/cv/', blank=True, null=True, verbose_name="CV")

    compagnie = models.ForeignKey(
        'compagnie.Compagnie',
        on_delete=models.CASCADE,
        related_name='chauffeurs',
        verbose_name="Compagnie"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chauffeur"
        verbose_name_plural = "Chauffeurs"
        ordering = ['nom_complet']

    def __str__(self):
        return self.nom_complet


class Convoyeur(models.Model):
    """Modèle représentant un convoyeur de la compagnie."""

    SITUATION_MATRIMONIALE_CHOICES = [
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié(e)'),
        ('divorce', 'Divorcé(e)'),
        ('veuf', 'Veuf/Veuve'),
    ]

    # Informations générales
    nom_complet = models.CharField(max_length=200, verbose_name="Nom complet")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")

    # Identité
    numero_cni = models.CharField(max_length=50, blank=True, verbose_name="Numéro CNI")
    situation_matrimoniale = models.CharField(
        max_length=20,
        choices=SITUATION_MATRIMONIALE_CHOICES,
        blank=True,
        verbose_name="Situation matrimoniale"
    )
    nombre_enfants = models.PositiveIntegerField(default=0, verbose_name="Nombre d'enfants en charge")

    # Coordonnées
    telephone_2 = models.CharField(max_length=20, blank=True, verbose_name="Deuxième téléphone")
    lieu_habitation = models.CharField(max_length=200, blank=True, verbose_name="Lieu d'habitation")

    # Contact d'urgence
    personne_urgence = models.CharField(max_length=200, blank=True, verbose_name="Personne à contacter en cas d'urgence")
    telephone_urgence = models.CharField(max_length=20, blank=True, verbose_name="Téléphone personne d'urgence")

    compagnie = models.ForeignKey(
        'compagnie.Compagnie',
        on_delete=models.CASCADE,
        related_name='convoyeurs',
        verbose_name="Compagnie"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Convoyeur"
        verbose_name_plural = "Convoyeurs"
        ordering = ['nom_complet']

    def __str__(self):
        return self.nom_complet
