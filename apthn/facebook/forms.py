from django import forms


class FacebookContactForm(forms.Form):
    email = forms.EmailField(help_text="Enter your email if you want to receive an email notification.", required=False)

    def contactstring(self, request):
        if self.cleaned_data['email']:
            return self.cleaned_data['email']
        else:
            return 'fb-%s' % request.facebook.uid
