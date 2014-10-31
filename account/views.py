from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import logout_then_login
from django.contrib import messages
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.conf import settings
from django import forms

from account.models import Invite, Player


class InviteForm(forms.Form):
    email = forms.EmailField(label='Invite by e-mail')


class RespondInviteForm(forms.Form):  # TODO add username
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Confirm password', widget=forms.PasswordInput)


def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('game.views.start'))

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user is None:
                messages.error(request, 'Invalid data')
                return HttpResponseRedirect(reverse('account.views.login'))
            else:
                try:
                    player = Player.objects.get(user=user)
                    django_login(request, user)
                    return HttpResponseRedirect(reverse('game.views.start'))
                except Player.DoesNotExist:
                    messages.error(request, 'User is not a player')
                    return HttpResponseRedirect(reverse('account.views.login'))

    else:
        form = AuthenticationForm(request)
    return render(request, 'Repower/home.html', {'form': form})


def logout(request):
    return logout_then_login(request)


def view_account(request):
    pass


@login_required
def edit_account(request):
    pass


@login_required
def invite(request):
    if request.method == 'POST':
        form = InviteForm(data=request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            if Invite.objects.filter(invitor=request.user).count() >= settings.MAX_INVITES_PER_USER:
                messages.error(request, 'You used up all your invites (%d)' % settings.MAX_INVITES_PER_USER)
            elif Invite.objects.filter(email=email).exists():
                messages.error(request, 'This recipient was already invited')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'You cannot invite this player')
            else:
                new_invite = Invite.objects.create_invite(email=email, invitor=Player.objects.get_by_user(request.user))
                send_mail(
                    'Invited to Repower',

                    '''Hello!

                    You have been invited by %s to play Repower. Create your account by acessing this URL:

                    %s

                    If you do not want to join Repower, simply ignore this message.

                    Love''' %
                    (request.user.username, reverse('account.views.respond_invite', kwargs={'code': new_invite.code})),

                    settings.INVITE_MAIL_SENDER_ADDRESS,
                    [email],
                    fail_silently=False
                )
                messages.success(request, 'An invite has been sent to %s' % email)
    else:
        form = InviteForm(request)
    return render(request, 'game/start.html', {'invite_form': form})


def respond_invite(request, code):
    if request.user.is_authenticated():
        messages.error(request, "Please log out first (and remember that multiple accounts per person are not allowed)")
        return HttpResponseRedirect(reverse('game.views.start'))

    invite = get_object_or_404(Invite, code=code)

    if not invite.valid:
        messages.error(request, "This invite cannot be used")
        return HttpResponseRedirect(reverse('Repower.views.home'))

    if User.objects.filter(email=invite.email).exists():
        invite.valid = False
        invite.save()
        messages.error(request, "This invite cannot be used")
        return HttpResponseRedirect(reverse('Repower.views.home'))

    if request.method == 'POST':
        form = RespondInviteForm(data=request.POST)
        if form.is_valid():
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            if password != password_confirm:
                messages.error(request, 'Your passwords do not match')
            else:
                new_player = invite.create_player(password)
                messages.success(request, 'Success! Please log in')
                return HttpResponseRedirect(reverse('Repower.views.home'))
    else:
        form = RespondInviteForm()
    return render(request, 'account/respond_invite.html', {'respond_form': form, 'invite': invite})