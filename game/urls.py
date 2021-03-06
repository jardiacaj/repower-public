from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^$', 'game.views.home', name='home'),
                       url(r'^login$', 'game.views.login', name='login'),
                       url(r'^logout$', 'game.views.logout', name='logout'),
                       url(r'^account$', 'game.views.view_own_account', name='view_own_account'),
                       url(r'^account/(?P<username>.+)$', 'game.views.view_account', name='view_account'),
                       url(r'^edit_account$', 'game.views.edit_account', name='edit_account'),
                       url(r'^invite$', 'game.views.game_invite', name='game_invite'),
                       url(r'^invite/(?P<code>\w+)$', 'game.views.respond_game_invite', name='respond_game_invite'),
                       url(r'^game$', 'game.views.start', name='start'),
                       url(r'^game/notifications$', 'game.views.notifications', name='notifications'),
                       url(r'^game/new_match$', 'game.views.new_match', name='new_match'),
                       url(r'^game/public_matches$', 'game.views.public_matches', name='public_matches'),
                       url(r'^match/(?P<match_pk>\d+)$', 'game.views.view_match', name='view_match'),
                       url(r'^match/(?P<match_pk>\d+)/invite$', 'game.views.match_invite', name='match_invite'),
                       url(r'^match/(?P<match_pk>\d+)/invite/(?P<player_pk>\d+)$', 'game.views.match_invite',
                           name='match_invite'),
                       url(r'^match/(?P<match_pk>\d+)/ready$', 'game.views.ready', name='ready'),
                       url(r'^match/(?P<match_pk>\d+)/leave$', 'game.views.leave', name='leave'),
                       url(r'^match/(?P<match_pk>\d+)/make_public$', 'game.views.make_public', name='make_public'),
                       url(r'^match/(?P<match_pk>\d+)/make_private$', 'game.views.make_private', name='make_private'),
                       url(r'^match/(?P<match_pk>\d+)/kick/(?P<player_pk>\d+)$', 'game.views.kick', name='kick'),
                       url(r'^match/(?P<match_pk>\d+)/add_command$', 'game.views.add_command', name='add_command'),
                       url(r'^match/(?P<match_pk>\d+)/delete_command/(?P<order>\d+)$', 'game.views.delete_command',
                           name='delete_command'),
                       url(r'^match/(?P<match_pk>\d+)/map$', 'game.views.view_map_in_match', name='view_map_in_match'),
                       url(r'^map/(?P<map_pk>\d+)$', 'game.views.view_map', name='view_map'),
                       url(r'^token/(?P<token_type_pk>\d+)$', 'game.views.view_token', name='view_token'),
)

# Do not forget to add unauthenticated access tests