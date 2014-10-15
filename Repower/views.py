from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render


def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('game.views.start'))
    return render(request, 'Repower/home.html', {'form': AuthenticationForm()})