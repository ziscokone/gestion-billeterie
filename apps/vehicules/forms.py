from django import forms
from .models import ModeleVehicule, Vehicule
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
        fields = ['modele', 'immatriculation', 'actif']
        widgets = {
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
        }
        labels = {
            'modele': 'Modèle de véhicule',
            'immatriculation': 'Numéro d\'immatriculation',
            'actif': 'Véhicule actif',
        }
