from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'login/$', 'account.views.login', name='login'),
                       url(r'logout/$', 'account.views.logout', name='logout'),
                       url(r'view_account/$', 'account.views.view_account', name='view_account'),
                       url(r'edit_account/$', 'account.views.edit_account', name='edit_account'),
                       url(r'invite/$', 'account.views.invite', name='invite'),
                       url(r'invite/(?P<code>\w+)$', 'account.views.respond_invite', name='respond_invite')
)
