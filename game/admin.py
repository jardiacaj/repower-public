from django.contrib import admin

from game import models


admin.site.register(models.Match)
admin.site.register(models.MatchPlayer)