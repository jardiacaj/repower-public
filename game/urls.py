from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^$', 'game.views.start', name='start'),
                       url(r'new_match$', 'game.views.new_match', name='new_match'),
                       url(r'match/(?P<match_pk>\d+)$', 'game.views.view_match', name='view_match'),
                       url(r'match/(?P<match_pk>\d+)/invite$', 'game.views.match_invite', name='match_invite'),
                       url(r'match/(?P<match_pk>\d+)/invite/(?P<player_pk>\d+)$', 'game.views.match_invite',
                           name='match_invite'),
                       url(r'match/(?P<match_pk>\d+)/ready$', 'game.views.ready', name='ready'),
                       url(r'match/(?P<match_pk>\d+)/leave', 'game.views.leave', name='leave'),
                       url(r'match/(?P<match_pk>\d+)/make_public', 'game.views.make_public', name='make_public'),
                       url(r'match/(?P<match_pk>\d+)/make_private', 'game.views.make_private', name='make_private'),
                       url(r'match/(?P<match_pk>\d+)/kick/(?P<player_pk>\d+)$', 'game.views.kick', name='kick'),
                       url(r'match/(?P<match_pk>\d+)/add_command', 'game.views.add_command', name='add_command'),
                       url(r'match/(?P<match_pk>\d+)/map', 'game.views.view_map_in_match', name='view_map_in_match'),
                       url(r'map/(?P<map_pk>\d+)$', 'game.views.view_map', name='view_map'),
                       url(r'token/(?P<token_type_pk>\d+)$', 'game.views.view_token', name='view_token'),
)

# TODO: public game listing and joining

# Do not forget to add unauthenticated access tests