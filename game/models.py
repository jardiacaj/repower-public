from django.db import models


class MatchManager(models.Manager):
    pass


class Match(models.Model):
    objects = MatchManager()


class MatchPlayerManager(models.Manager):
    pass


class MatchPlayer(models.Model):
    objects = MatchPlayerManager()

    match = models.ForeignKey(Match)

