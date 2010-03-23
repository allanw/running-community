from django import forms
from alsapp.models import Poll

class PollForm(forms.ModelForm):
	
    class Meta:
        model = Poll