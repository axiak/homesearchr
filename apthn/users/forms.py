from django import forms
from models import AptHunter

class UserForm(forms.Form):
    email = forms.EmailField(help_text="Where would you like to be notified", required=False)
    username = forms.CharField(help_text="(optional) Give a username to log in with", required=False)
    password = forms.CharField(widget=forms.PasswordInput,help_text="(optional) password", required=False)
    password2 = forms.CharField(widget=forms.PasswordInput,help_text="password again", required=False)

    # i wonder whats this for
    contactstring = lambda f,x: f.cleaned_data['email']

    def clean(self):
        c = self.cleaned_data
        if not AptHunter.name_available(c.get("username")):
            raise forms.ValidationError("Username is already taken.  Try adding some numbers, those look cool")
        password1 = c.get("password")
        password2 = c.get("password2")
        if password1 != password2:
            raise forms.ValidationError("Password mismatch.  Try again.")
        return c

class ResetForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput,help_text="Password (again)")
