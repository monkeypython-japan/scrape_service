from django import forms
from .models import ScrapeTarget

class ScrapeTargetForm(forms.ModelForm):
    class Meta:
        model = ScrapeTarget
        fields = ('owner','name','url','xpath','interval','trigger_number','description')
 #      exclude = ('owner',)