from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models

from account.models import Player


class PlayerCannotJoinMatch(Exception):
    pass


class MatchIsFull(Exception):
    pass


class MatchInWrongStatus(Exception):
    pass


class MatchPlayerAlreadyReady(Exception):
    pass


class CannotKickOwner(Exception):
    pass


class Map(models.Model):
    num_seats = models.IntegerField()
    name = models.CharField(max_length=30)
    image_file_name = models.CharField(max_length=30)
    public = models.BooleanField()

    def __str__(self):
        return self.name


class MapCountry(models.Model):
    class Meta:
        verbose_name_plural = "Map countries"

    map = models.ForeignKey(Map, related_name='countries')
    name = models.CharField(max_length=30)
    reserve = models.ForeignKey('MapRegion', related_name='reserve_players')
    headquarters = models.ForeignKey('MapRegion', related_name='headquarters_players')

    def __str__(self):
        return "%s in %s" % (self.name, self.map.name)


class MapRegion(models.Model):
    map = models.ForeignKey(Map)
    country = models.ForeignKey(MapCountry, blank=True, null=True)
    name = models.CharField(max_length=30)
    short_name = models.CharField(max_length=3)
    land = models.BooleanField()
    water = models.BooleanField()
    render_on_map = models.BooleanField(default=True)
    position_x = models.PositiveSmallIntegerField(default=0)
    position_y = models.PositiveSmallIntegerField(default=0)
    size_x = models.PositiveSmallIntegerField(default=0)
    size_y = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return "%s in %s" % (self.name, self.map.name)


class MapRegionLink(models.Model):
    source = models.ForeignKey(MapRegion, related_name='links_source')
    destination = models.ForeignKey(MapRegion, related_name='links_destination')
    unidirectional = models.BooleanField(default=False)
    crossing_water = models.BooleanField(default=False)

    def validate_unique(self, exclude=None):
        if self.objects.filter(source=self.source, destination=self.destination).exists():
            raise ValidationError("Equivalent MapRegionLink exists")
        if self.objects.filter(source=self.destination, destination=self.source).exists():
            raise ValidationError("Reversed equivalent MapRegionLink exists")

    def __str__(self):
        return "%s to %s" % (self.source.name, self.destination)


class Turn(models.Model):
    match = models.ForeignKey('Match')
    number = models.PositiveIntegerField()

    def __str__(self):
        return "%d in %s" % (self.number, self.match.name)


class BoardTokenType(models.Model):
    name = models.CharField(max_length=30)
    short_name = models.CharField(max_length=3)
    movements = models.PositiveSmallIntegerField()
    strength = models.PositiveSmallIntegerField()
    # TODO: special units

    def __str__(self):
        return self.name


class PlayerInTurn(models.Model):
    class Meta:
        verbose_name_plural = "Players in turn"

    turn = models.ForeignKey(Turn)
    match_player = models.ForeignKey('MatchPlayer')
    power_points = models.PositiveSmallIntegerField()
    flag_controlled_by = models.ForeignKey('PlayerInTurn')

    def __str__(self):
        return "%s in %s (turn %d)" % (
            self.match_player.player.user.username, self.match_player.match.name, self.turn.number)


class BoardToken(models.Model):
    owner = models.ForeignKey(PlayerInTurn)
    position = models.ForeignKey(MapRegion)
    type = models.ForeignKey(BoardTokenType)

    def __str__(self):
        return "%s in %s from %s" % (self.type.name, self.position.name, self.owner)


class Movement(models.Model):
    TYPE_MOVE = 'MOV'
    TYPE_CONVERT = 'CON'
    TYPE_BUILD_MEGA_MISSILE = 'MMI'
    TYPES = (
        (TYPE_MOVE, 'Move'),
        (TYPE_CONVERT, 'Conversion'),
        (TYPE_BUILD_MEGA_MISSILE, 'Mega-missile'),
    )

    player_in_turn = models.ForeignKey(PlayerInTurn)
    type = models.CharField(max_length=3, choices=TYPES)

    def __str__(self):
        return self.player_in_turn.__str__()


class MatchManager(models.Manager):
    def create_match(self, name, owner, map):
        match = self.create(name=name, owner=owner, map=map, status=Match.STATUS_SETUP)
        return match

    def get_by_player(self, player):
        return self.filter(players__player=player)


class Match(models.Model):
    class Meta:
        verbose_name_plural = "Matches"

    objects = MatchManager()

    STATUS_SETUP = 'SET'
    STATUS_SETUP_ABORTED = 'SUA'
    STATUS_PLAYING = 'PLA'
    STATUS_PAUSED = 'PAU'
    STATUS_FINISHED = 'FIN'
    STATUS_ABORTED = 'ABO'
    STATUSES = (
        (STATUS_SETUP, 'Set up'),
        (STATUS_SETUP_ABORTED, 'Aborted (when in setup)'),
        (STATUS_PLAYING, 'Playing'),
        (STATUS_PAUSED, 'Paused'),
        (STATUS_FINISHED, 'Finished'),
        (STATUS_ABORTED, 'Aborted (when in progress)'),
    )

    name = models.CharField(max_length=50)
    owner = models.ForeignKey(Player, related_name='owner_of')
    map = models.ForeignKey(Map, related_name='matches')
    status = models.CharField(max_length=3, choices=STATUSES)
    public = models.BooleanField(default=False)

    def join_player(self, player):
        if self.status != self.STATUS_SETUP:
            raise MatchInWrongStatus()
        if self.players.count() >= self.map.num_seats:
            raise MatchIsFull()
        if player not in Player.objects.get_match_candidates(self):
            raise PlayerCannotJoinMatch()
        MatchPlayer.objects.create_player(self, player)

    def match_player_ready(self, match_player):
        if self.status in (self.STATUS_ABORTED, self.STATUS_FINISHED, self.STATUS_SETUP_ABORTED):
            raise MatchInWrongStatus()
        if self.map.num_seats == self.players.count():
            all_ready = True
            for player in self.players.all():
                if not player.ready:
                    all_ready = False
            if all_ready:
                self.all_players_ready()

    def all_players_ready(self):
        if self.status == self.STATUS_SETUP:
            self.transition_from_setup_to_playing()
        else:
            raise MatchInWrongStatus()
        for player in self.players.all():
            player.ready = False
            player.save()

    def transition_from_setup_to_playing(self):
        self.status = self.STATUS_PLAYING
        self.save()

    def url(self):
        return reverse('game.views.view_match', kwargs={'match_pk': self.pk})

    def __str__(self):
        return self.name


class MatchPlayerManager(models.Manager):
    def create_player(self, match, player):
        match_player = self.create(match=match, player=player)
        return match_player

    def get_by_match_and_player(self, match, player):
        return self.get(match=match, player=player)


class MatchPlayer(models.Model):
    objects = MatchPlayerManager()

    match = models.ForeignKey(Match, related_name='players')
    player = models.ForeignKey(Player, related_name='match_players')
    ready = models.BooleanField(default=False)
    country = models.ForeignKey(MapCountry, related_name='players', blank=True, null=True)

    def kick(self):
        if self.match.status != Match.STATUS_SETUP:
            raise MatchInWrongStatus()
        if self.match.owner == self:
            raise CannotKickOwner()
        self.delete()

    def leave(self):
        if self.match.status != Match.STATUS_SETUP:
            raise MatchInWrongStatus()
        if self.match.owner.pk == self.pk:
            self.match.status = Match.STATUS_SETUP_ABORTED
            self.match.save()
        else:
            self.delete()

    def make_ready(self):
        if self.ready:
            raise MatchPlayerAlreadyReady
        self.ready = True
        self.save()
        self.match.match_player_ready(self)

    def __str__(self):
        return '%s in %s' % (self.player.user.username, self.match.name)

