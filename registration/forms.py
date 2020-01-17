from django import forms
from .models import ScrapeTarget

class ScrapeTargetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owner'].widget = forms.HiddenInput()

    class Meta:
        model = ScrapeTarget
        fields = ('owner','name','url','xpath','interval','trigger_number','description')
