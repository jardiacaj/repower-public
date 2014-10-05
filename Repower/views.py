from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render


def home(request):
    return render(request, 'Repower/home.html', {'form': AuthenticationForm()})