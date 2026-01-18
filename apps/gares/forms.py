from django import forms
from .models import Gare


class GareForm(forms.ModelForm):
    """Formulaire pour créer/modifier une gare."""

    class Meta:
        model = Gare
        fields = ['nom', 'code', 'ville', 'adresse', 'telephone', 'compagnie', 'active']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la gare'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CKY', 'maxlength': 10}),
            'ville': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse complète'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone'}),
            'compagnie': forms.Select(attrs={'class': 'form-select'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
        return code
