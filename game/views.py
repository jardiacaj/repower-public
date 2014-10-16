from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from account.models import Player
from account.views import InviteForm
from game.models import Match, MatchPlayer, PlayerCannotJoinMatch, MatchIsFull, MatchInWrongStatus, \
    MatchPlayerAlreadyReady, Map


class MatchCreationForm(forms.Form):
    name = forms.CharField(label='Match name')
    map = forms.ModelChoiceField(label='Map', queryset=Map.objects.filter(public=True))


@login_required
def start(request):
    return render(
        request,
        'game/start.html',
        {
            'invite_form': InviteForm(),
            'match_players': MatchPlayer.objects.filter(player=Player.objects.get_by_user(request.user))
        }
    )


@login_required
def new_match(request):
    if request.method == 'POST':
        form = MatchCreationForm(data=request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            map = form.cleaned_data['map']
            current_player = Player.objects.get_by_user(request.user)
            match = Match.objects.create_match(name, current_player, map)
            MatchPlayer.objects.create_player(match, current_player)
            return HttpResponseRedirect(match.get_absolute_url())
    else:
        form = MatchCreationForm()
    return render(request, 'game/new_match.html', {'setup_form': form})


@login_required
def match_invite(request, match_pk, player_pk=None):
    match = get_object_or_404(Match, pk=match_pk)

    if player_pk is not None:
        player = get_object_or_404(Player, pk=player_pk)
        if not match.owner.user == request.user and not (match.public and match.players.get(player=player)):
            messages.error(request, 'Only the owner can invite in private games')
            return HttpResponseRedirect(match.get_absolute_url())
        try:
            match.join_player(player)
            return HttpResponseRedirect(match.get_absolute_url())
        except PlayerCannotJoinMatch:
            messages.error(request, 'This player can not be invited')
        except MatchIsFull:
            messages.error(request, 'Match is full')
            return HttpResponseRedirect(match.get_absolute_url())
        except MatchInWrongStatus:
            messages.error(request, 'Match is no longer in set up phase')
            return HttpResponseRedirect(match.get_absolute_url())

    candidates = Player.objects.get_match_candidates(match)
    return render(request, 'game/match_invite.html', {'match': match, 'candidates': candidates})


@login_required
def view_match(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)
    player = Player.objects.get_by_user(request.user)

    if not MatchPlayer.objects.filter(match=match, player=player).exists():
        return HttpResponse("Viewing matches where you don't participate is not yet implemented")  # TODO
    elif match.status == match.STATUS_SETUP_ABORTED:
        return HttpResponse("Viewing aborted matches is not yet implemented")  # TODO
    elif match.status == match.STATUS_SETUP:
        return render(request, 'game/setup_match.html', {'match': match})
    elif match.status == match.STATUS_PLAYING:
        return render(request, 'game/play_match.html', {'match': match})


@login_required
def ready(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)
    player = Player.objects.get_by_user(request.user)
    match_player = MatchPlayer.objects.get_by_match_and_player(match, player)
    try:
        match_player.make_ready()
    except MatchPlayerAlreadyReady:
        messages.error(request, "You are already ready")
    except MatchInWrongStatus:
        messages.error(request, "The current game status doesn't allow you to be ready")
    return HttpResponseRedirect(match.get_absolute_url())


@login_required
def make_public(request, match_pk):
    return change_public(request, match_pk, True)


@login_required
def make_private(request, match_pk):
    return change_public(request, match_pk, False)


@login_required
def change_public(request, match_pk, public):
    match = get_object_or_404(Match, pk=match_pk)

    if not match.owner.user == request.user:
        messages.error(request, 'Only the owner can change this')
    elif not match.status == Match.STATUS_SETUP:
        messages.error(request, 'Match is no longer in set up phase')
    else:
        match.public = public
        match.save()
        messages.success(request, "This game is now public" if public else "This game is now private")

    return HttpResponseRedirect(match.get_absolute_url())


@login_required
def kick(request, match_pk, player_pk):
    match = get_object_or_404(Match, pk=match_pk)
    player_to_kick = get_object_or_404(Player, pk=player_pk)
    match_player_to_kick = MatchPlayer.objects.get_by_match_and_player(match, player_to_kick)
    player = Player.objects.get_by_user(request.user)

    if player != match.owner:
        messages.error(request, "Only the match owner can kick players")
    else:
        match_player_to_kick.kick()

    return HttpResponseRedirect(match.get_absolute_url())


@login_required
def leave(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)
    player = Player.objects.get_by_user(request.user)
    match_player = MatchPlayer.objects.get_by_match_and_player(match, player)
    match_player.leave()
    return HttpResponseRedirect(match.get_absolute_url())