from game.models import Player


def player_processor(request):
    if request.user.is_authenticated():
        player = Player.objects.get_by_user(request.user)
        return {'player': player}
    return dict()
