from django import forms
from .models import ModeleVehicule, Vehicule, ReparationVehicule
import json


class ModeleVehiculeForm(forms.ModelForm):
    """Formulaire pour créer et modifier un modèle de véhicule."""

    class Meta:
        model = ModeleVehicule
        fields = ['marque', 'nom', 'capacite', 'disposition_sieges']
        widgets = {
            'marque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Mercedes-Benz'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Sprinter 516'
            }),
            'capacite': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 20',
                'min': '1'
            }),
            'disposition_sieges': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': '''Exemple de disposition en JSON:
{
  "colonnes": 5,
  "rangees": [
    [1, 2, null, 3, 4],
    [5, 6, null, 7, 8],
    [9, 10, null, 11, 12]
  ],
  "sieges_non_vendables": [1]
}'''
            }),
        }
        labels = {
            'marque': 'Marque',
            'nom': 'Nom du modèle',
            'capacite': 'Capacité (nombre de places)',
            'disposition_sieges': 'Disposition des sièges (JSON)',
        }
        help_texts = {
            'disposition_sieges': 'Configuration JSON de la disposition des sièges. Utiliser null pour les espaces vides (couloirs).',
        }

    def clean_disposition_sieges(self):
        """Valider le format JSON de la disposition."""
        data = self.cleaned_data.get('disposition_sieges')
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError('Format JSON invalide.')

        # Validation de la structure
        if not isinstance(data, dict):
            raise forms.ValidationError('La disposition doit être un objet JSON.')

        if 'colonnes' not in data or 'rangees' not in data:
            raise forms.ValidationError('Les clés "colonnes" et "rangees" sont requises.')

        if not isinstance(data['rangees'], list):
            raise forms.ValidationError('Les rangées doivent être une liste.')

        return data


class VehiculeForm(forms.ModelForm):
    """Formulaire pour créer et modifier un véhicule."""

    class Meta:
        model = Vehicule
        fields = [
            # Informations générales
            'modele', 'immatriculation', 'actif', 'notes',
            # Caractéristiques techniques
            'numero_chassis', 'annee_fabrication', 'date_mise_circulation',
            'type_carburant', 'type_boite',
            # Documents & conformité légale
            'compagnie_assurance', 'date_expiration_assurance',
            'date_expiration_visite_technique', 'date_expiration_carte_grise',
            'date_expiration_licence_transport'
        ]
        widgets = {
            # Informations générales
            'modele': forms.Select(attrs={
                'class': 'form-select',
            }),
            'immatriculation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: GN-1234-AB'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notes et observations sur le véhicule...'
            }),
            # Caractéristiques techniques
            'numero_chassis': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: WDD9066051P123456'
            }),
            'annee_fabrication': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 2020',
                'min': '1990',
                'max': '2030'
            }),
            'date_mise_circulation': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'type_carburant': forms.Select(attrs={
                'class': 'form-select',
            }),
            'type_boite': forms.Select(attrs={
                'class': 'form-select',
            }),
            # Documents & conformité légale
            'compagnie_assurance': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Allianz Assurances Guinée'
            }),
            'date_expiration_assurance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_expiration_visite_technique': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_expiration_carte_grise': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_expiration_licence_transport': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            # Informations générales
            'modele': 'Modèle de véhicule',
            'immatriculation': 'Numéro d\'immatriculation',
            'actif': 'Véhicule actif',
            'notes': 'Notes et observations',
            # Caractéristiques techniques
            'numero_chassis': 'Numéro de châssis (VIN)',
            'annee_fabrication': 'Année de fabrication',
            'date_mise_circulation': 'Date de mise en circulation',
            'type_carburant': 'Type de carburant',
            'type_boite': 'Type de boîte de vitesse',
            # Documents & conformité légale
            'compagnie_assurance': 'Compagnie d\'assurance',
            'date_expiration_assurance': 'Date d\'expiration assurance',
            'date_expiration_visite_technique': 'Date d\'expiration visite technique',
            'date_expiration_carte_grise': 'Date d\'expiration carte grise',
            'date_expiration_licence_transport': 'Date d\'expiration licence de transport',
        }


class ReparationVehiculeForm(forms.ModelForm):
    """Formulaire pour créer et modifier une réparation."""

    class Meta:
        model = ReparationVehicule
        fields = [
            'vehicule', 'date_reparation', 'type_reparation', 'description',
            'garage_prestataire', 'montant', 'kilometrage', 'pieces_remplacees',
            'statut'
        ]
        widgets = {
            'vehicule': forms.Select(attrs={
                'class': 'form-select',
            }),
            'date_reparation': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'type_reparation': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Décrire la réparation effectuée...'
            }),
            'garage_prestataire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Garage Central Auto'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 250000',
                'min': '0',
                'step': '0.01'
            }),
            'kilometrage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 145000',
                'min': '0'
            }),
            'pieces_remplacees': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Ex: Embrayage, Disques de frein avant...'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'vehicule': 'Véhicule',
            'date_reparation': 'Date de réparation',
            'type_reparation': 'Type de réparation',
            'description': 'Description',
            'garage_prestataire': 'Garage/Prestataire',
            'montant': 'Montant (FCFA)',
            'kilometrage': 'Kilométrage (optionnel)',
            'pieces_remplacees': 'Pièces remplacées (optionnel)',
            'statut': 'Statut',
        }
