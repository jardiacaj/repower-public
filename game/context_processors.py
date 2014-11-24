from game.models import Player


def player_processor(request):
    if request.user.is_authenticated():
        try:
            player = Player.objects.get_by_user(request.user)
        except Player.DoesNotExist:
            player = None
        return {'player': player}
    return dict()
