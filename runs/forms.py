from django import forms
from runs.models import Poll

class PollForm(forms.ModelForm):
	
    class Meta:
        model = Poll