from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from account.models import Player
from account.views import InviteForm
from game.models import Match, MatchPlayer, PlayerCannotJoinMatch, MatchIsFull, MatchInWrongStatus, \
    MatchPlayerAlreadyReady, Map, BoardTokenType, TokenConversion, TokenValueConversion, MapCountry, MapRegion, Command, \
    Turn, PlayerInTurn


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
            return HttpResponseRedirect(reverse('game.views.match_invite', kwargs={'match_pk': match.id}))
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
    if not match.can_view_match(player):
        messages.error(request, "You can not see this match because it's private and you are not playing in it")
        return HttpResponseRedirect(reverse('game.views.start'))

    token_types = BoardTokenType.objects.all()
    conversions = TokenConversion.objects.all()
    value_conversions = TokenValueConversion.objects.all()

    match_player = MatchPlayer.objects.get_by_match_and_player(match, player)
    is_owner = (player == match.owner)
    client_is_in_game = match_player in match.players.all()

    context = {
        'match': match,
        'player': player,
        'match_player': match_player,
        'client_is_in_game': client_is_in_game,
        'is_owner': is_owner,
        'token_types': token_types,
        'conversions': conversions,
        'value_conversions': value_conversions,
    }

    if match.has_started():
        turn_number = request.GET.get('turn', match.latest_turn().number)
        try:
            turn = Turn.objects.get(match=match, number=turn_number)
        except Turn.DoesNotExist:
            turn = match.latest_turn()

        player_in_turn = None if not client_is_in_game else \
            PlayerInTurn.objects.get(match_player__match=match, match_player__player=player, turn=turn)
        is_latest_turn = (turn == match.latest_turn())

        context = dict(list(context.items()) + list({
                                                        'player_in_turn': player_in_turn,
                                                        'turn': turn,
                                                        'is_latest_turn': is_latest_turn,
                                                    }.items()))

    context['can_add_commands'] = \
        False if not client_is_in_game or not match.is_in_progress() else player_in_turn.can_add_commands()

    if match.status == match.STATUS_SETUP_ABORTED:
        return HttpResponse("Viewing aborted matches is not yet implemented")  # TODO
    elif match.status == match.STATUS_SETUP:
        return render(request, 'game/setup_match.html', context)
    else:
        return render(request, 'game/play_match.html', context)


@login_required()
def view_map_in_match(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)
    player = Player.objects.get_by_user(request.user)

    if not match.can_view_match(player):
        messages.error(request, "You can not see this match because it's private and you are not playing in it")
        return HttpResponseRedirect(reverse('game.views.start'))

    turn_number = request.GET.get('turn', match.latest_turn().number)
    try:
        turn = Turn.objects.get(match=match, number=turn_number)
    except Turn.DoesNotExist:
        turn = match.latest_turn()

    response = HttpResponse(content_type="image/png")
    match.map.image_in_match(turn).save(response, "PNG")
    return response


def view_map(request, map_pk):
    show_debug = request.GET.get('show_debug', False)
    show_links = request.GET.get('show_links', False)
    response = HttpResponse(content_type="image/png")
    get_object_or_404(Map, pk=map_pk).image(show_debug, show_links).save(response, "PNG")
    return response


def view_token(request, token_type_pk):
    country_pk = request.GET.get('country', None)
    if country_pk is not None:
        country = MapCountry.objects.get(pk=country_pk)
    else:
        country = None

    response = HttpResponse(content_type="image/png")
    get_object_or_404(BoardTokenType, pk=token_type_pk).image(country).save(response, "PNG")
    return response


@login_required
def ready(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)
    player = Player.objects.get_by_user(request.user)
    match_player = MatchPlayer.objects.get_by_match_and_player(match, player)
    if match_player is None:
        messages.error(request, "You are not playing in this game")
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
    elif match_player_to_kick is None:
        messages.error(request, "This player is not in this game")
    else:
        match_player_to_kick.kick()

    return HttpResponseRedirect(match.get_absolute_url())


@login_required
def leave(request, match_pk):  # TODO: missing link on play_match template
    match = get_object_or_404(Match, pk=match_pk)
    player = Player.objects.get_by_user(request.user)
    match_player = MatchPlayer.objects.get_by_match_and_player(match, player)
    if match_player is not None:
        match_player.leave()
    else:
        messages.error(request, "You are not participating in that game")
    return HttpResponseRedirect(match.get_absolute_url())


@login_required
def add_command(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)
    player = Player.objects.get_by_user(request.user)
    match_player = MatchPlayer.objects.get_by_match_and_player(match, player)

    if match_player is None:
        messages.error(request, "You are not playing in this match")
    elif request.method != 'POST':
        messages.error(request, "Post me a command")
    elif not match_player.latest_player_in_turn().can_add_commands():
        messages.error(request, "You can not add more commands this turn")
    else:

        if request.POST.get('command_type') == 'move':
            try:
                token_type = BoardTokenType.objects.get(id=request.POST.get('move_token_type'))
                region_from = MapRegion.objects.get(id=request.POST.get('move_region_from'))
                region_to = MapRegion.objects.get(id=request.POST.get('move_region_to'))

                command = Command(
                    player_in_turn=match_player.latest_player_in_turn(),
                    order=Command.objects.filter(player_in_turn=match_player.latest_player_in_turn()).count(),
                    type=Command.TYPE_MOVEMENT,
                    token_type=token_type,
                    location=region_from,
                    move_destination=region_to
                )

                if command.can_be_added():
                    command.save()
                    messages.success(request, "Added movement command")

            except BoardTokenType.DoesNotExist:
                messages.error(request, "Invalid token type")
            except (MapRegion.DoesNotExist, Command.InvalidLocation):
                messages.error(request, "Invalid location(s)")

        elif request.POST.get('command_type') == 'buy':
            try:
                token_type = BoardTokenType.objects.get(id=request.POST.get('buy_token_type'))

                command = Command(
                    player_in_turn=match_player.latest_player_in_turn(),
                    order=Command.objects.filter(player_in_turn=match_player.latest_player_in_turn()).count(),
                    type=Command.TYPE_PURCHASE,
                    token_type=token_type
                )

                if command.can_be_added():
                    command.save()
                    messages.success(request, "Added purchase command")

            except (BoardTokenType.DoesNotExist, Command.TokenNotPurchasable):
                messages.error(request, "Invalid token type")

        elif request.POST.get('command_type') == 'convert':
            try:
                conversion = TokenConversion.objects.get(id=request.POST.get('convert_id'))
                location = MapRegion.objects.get(id=request.POST.get('convert_region'))

                command = Command(
                    player_in_turn=match_player.latest_player_in_turn(),
                    order=Command.objects.filter(player_in_turn=match_player.latest_player_in_turn()).count(),
                    type=Command.TYPE_CONVERSION,
                    conversion=conversion,
                    location=location
                )

                if command.can_be_added():
                    command.save()
                    messages.success(request, "Added conversion command")

            except TokenConversion.DoesNotExist:
                messages.error(request, "Invalid conversion")
            except (MapRegion.DoesNotExist, Command.InvalidLocation):
                messages.error(request, "Invalid location")

        else:
            messages.error(request, "Invalid command type")

    return HttpResponseRedirect(match.get_absolute_url())