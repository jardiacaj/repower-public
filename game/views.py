from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from account.views import InviteForm


@login_required
def start(request):
    return render(request, 'game/start.html', {'invite_form': InviteForm()})
