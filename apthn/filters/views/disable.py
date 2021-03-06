from django.views.generic.simple import direct_to_template

from apthn.filters.models import AptFilter
from apthn.filters.forms import DisableFilterForm

__all__ = ('disable_filter',)

def disable_filter(request, key):
    #class DisableFilterForm(forms.Form):
    aptf = AptFilter.all().filter("disable_string =", key).filter("active =", True).get()
    if not aptf:
        raise Http404("Could not find disable string")
    if request.method == "POST":
        form = DisableFilterForm(request.POST)
        if form.is_valid():
            aptf.disable_status = '%s,%s' % tuple((form.cleaned_data[x]
                                             for x in ('helpful', 'result')))
            aptf.active = False
            aptf.put()
            return direct_to_template(request, 'disablefilter-success.html')
    else:
        form = DisableFilterForm()
    return direct_to_template(request, 'disablefilter.html',
                              {'form': form})

