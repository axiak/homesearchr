from django import forms

TROOLEAN = ((-1, "Don't care"),
            (1, "Yes"),
            (0, "No"))


class DisableFilterForm(forms.Form):
    helpful = forms.ChoiceField(choices=(("", "-------"),
                                         ("Not helpful", "Not helpful"),
                                         ("Somewhat helpful", "Somewhat helpful"),
                                         ("Very helpful", "Very helpful"),
                                         ),
                                label="I found this site")
    result = forms.ChoiceField(choices=(("", "------"),
                                        ("No", "No"),
                                        ("Yes", "Yes")),
                               label="I was able to find a place")

class EmailForm(forms.Form):
    required_css_class = "required"

    email = forms.EmailField(help_text="Where would you like to be notified?")

    def contactstring(self, request):
        return self.cleaned_data['email']
    

class FilterForm(forms.Form):
    required_css_class = "required"

    expires = forms.DateField(help_text="Until when do you want notifications?")

    size = forms.MultipleChoiceField(choices=
                                     (
            ('studio', 'Studio'),
            ('1BR', '1BR'),
            ('2BR', '2BR'),
            ('3BR', '3BR'),
            ('4BR', '4BR'),
            ('5BR', '5BR'),
            ('6BR', '6BR')),
                                     help_text="What kind of size are you looking for? (You can select multiple.)")

    cats = forms.ChoiceField(choices=TROOLEAN,
                             help_text="Do you want cats to be permitted?")

    concierge = forms.ChoiceField(choices=TROOLEAN,
                             help_text="Do you want a concierge?")

    washerdryer = forms.ChoiceField(choices=TROOLEAN,
                                    label = 'Washer/Dryer',
                             help_text="Washer/dryer in the unit.")

    heat = forms.ChoiceField(choices=TROOLEAN,
                             help_text="Do you want heat included?")

    hotwater = forms.ChoiceField(choices=TROOLEAN,
                                 label="Hot Water",
                             help_text="Do you want hot water included?")

    brokerfee = forms.ChoiceField(choices=TROOLEAN,
                                  label="Broker Fee",
                             help_text="Do you want a broker fee?")
