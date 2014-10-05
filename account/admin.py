from django.contrib import admin

from account import models


admin.site.register(models.Invite)
admin.site.register(models.Player)