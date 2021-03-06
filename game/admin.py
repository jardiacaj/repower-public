from django.contrib import admin

from game import models


admin.site.register(models.BoardToken)
admin.site.register(models.BoardTokenType)
admin.site.register(models.Command)
admin.site.register(models.Invite)
admin.site.register(models.Map)
admin.site.register(models.MapCountry)
admin.site.register(models.MapRegion)
admin.site.register(models.MapRegionLink)
admin.site.register(models.Match)
admin.site.register(models.MatchPlayer)
admin.site.register(models.Player)
admin.site.register(models.PlayerInTurnStep)
admin.site.register(models.TokenConversion)
admin.site.register(models.TokenValueConversion)
admin.site.register(models.Turn)
