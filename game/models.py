from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Sum

from account.models import Player



# TODO sensible DB indexes


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
    num_seats = models.IntegerField(help_text="Number of seats of this map")
    name = models.CharField(max_length=30)
    image_file_name = models.CharField(max_length=30)
    public = models.BooleanField(default=False, help_text="Public maps can be used when players set up a new match")

    def __str__(self):
        return "%s (%d players)" % (self.name, self.num_seats)


class MapCountry(models.Model):
    class Meta:
        verbose_name_plural = "Map countries"

    map = models.ForeignKey(Map, related_name='countries')
    name = models.CharField(max_length=30)
    reserve = models.ForeignKey('MapRegion', related_name='countries_with_this_reserve')
    headquarters = models.ForeignKey('MapRegion', related_name='countries_with_this_headquarter')
    color_rgb = models.CharField(max_length=6)
    color_gif_palette = models.PositiveSmallIntegerField()

    def __str__(self):
        return "%s in %s" % (self.name, self.map.name)


class MapRegion(models.Model):
    map = models.ForeignKey(Map, related_name='regions')
    country = models.ForeignKey(MapCountry, blank=True, null=True)
    name = models.CharField(max_length=30)
    short_name = models.CharField(max_length=3)
    land = models.BooleanField(default=False)
    water = models.BooleanField(default=False)
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
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "%d in %s" % (self.number, self.match.name)


class BoardTokenType(models.Model):
    name = models.CharField(max_length=30)
    short_name = models.CharField(max_length=3)
    image_file_name = models.CharField(max_length=30)
    movements = models.PositiveSmallIntegerField(help_text="Number of tiles this token can cross in one move")
    strength = models.PositiveSmallIntegerField()
    purchasable = models.BooleanField(default=False,
                                      help_text="Purchasable tokens can be bought with power points"
                                                "equivalent to their strength")
    one_water_cross_per_movement = models.BooleanField(default=False)
    can_be_on_land = models.BooleanField(default=False)
    can_be_on_water = models.BooleanField(default=False)

    special_missile = models.BooleanField(default=False)
    special_attack_reserves = models.BooleanField(default=False, help_text="Can attack reserves")
    special_destroys_all = models.BooleanField(default=False, help_text="Infinite strength, beats all")

    def __str__(self):
        return self.name


class TokenConversion(models.Model):
    needs = models.ForeignKey(BoardTokenType, related_name="conversions_sourced")
    needs_quantity = models.PositiveSmallIntegerField(default=3)
    produces = models.ForeignKey(BoardTokenType, related_name="conversions_producing")
    produces_quantity = models.PositiveSmallIntegerField(default=1)


class TokenValueConversion(models.Model):
    from_points = models.BooleanField(default=False)
    from_tokens = models.BooleanField(default=False)
    needs_value = models.PositiveSmallIntegerField()
    produces = models.ForeignKey(BoardTokenType, related_name="value_conversions_producing")


class PlayerInTurn(models.Model):
    class Meta:
        verbose_name_plural = "Players in turn"

    turn = models.ForeignKey(Turn)
    match_player = models.ForeignKey('MatchPlayer', related_name='+')
    power_points = models.PositiveSmallIntegerField()
    flag_controlled_by = models.ForeignKey('MatchPlayer', related_name='+', blank=True, null=True)
    total_strength = models.PositiveIntegerField(default=0)
    timeout_requested = models.BooleanField(default=False)
    ready = models.BooleanField(default=False)
    left_match = models.BooleanField(default=False)

    def calculate_total_strength(self):
        self.total_strength = self.tokens.aggregate(Sum('type__strength'))['type__strength__sum']
        return self.total_strength

    def make_ready(self):
        if self.match_player.match.status not in (Match.STATUS_PLAYING, Match.STATUS_PAUSED):
            raise MatchInWrongStatus()
        self.ready = True
        self.save()
        self.match.match_player_ready(self.match_player)

    def __str__(self):
        return "%s in %s (turn %d)" % (
            self.match_player.player.user.username, self.match_player.match.name, self.turn.number)


class BoardToken(models.Model):
    owner = models.ForeignKey(PlayerInTurn, related_name='tokens')
    position = models.ForeignKey(MapRegion)
    type = models.ForeignKey(BoardTokenType)
    moved_this_turn = models.BooleanField(default=False)
    can_move_this_turn = models.BooleanField(default=True)
    retreat_from_draw = models.BooleanField(default=False)

    def __str__(self):
        return "%s in %s from %s" % (self.type.name, self.position.name, self.owner)


class Command(models.Model):
    TYPE_MOVEMENT = 'MOV'
    TYPE_CONVERSION = 'TCO'
    TYPE_VALUE_CONVERSION = 'VCO'
    TYPE_PURCHASE = 'BUY'
    TYPES = (
        (TYPE_MOVEMENT, 'Move'),
        (TYPE_CONVERSION, 'Token conversion'),
        (TYPE_VALUE_CONVERSION, 'Value conversion'),
        (TYPE_PURCHASE, 'Token purchase')
    )

    player_in_turn = models.ForeignKey(PlayerInTurn)
    order = models.PositiveSmallIntegerField()
    type = models.CharField(max_length=3, choices=TYPES)
    location = models.ForeignKey(MapRegion, null=True, blank=True, related_name='+')
    valid = models.NullBooleanField()

    buy_type = models.ForeignKey(BoardTokenType, null=True, blank=True, related_name='+')
    move_destination = models.ForeignKey(MapRegion, null=True, blank=True, related_name='+')
    conversion = models.ForeignKey(TokenConversion, null=True, blank=True, related_name='+')
    value_conversion = models.ForeignKey(TokenConversion, null=True, blank=True, related_name='+')
    # TODO Value conversion token types

    def __str__(self):
        return self.player_in_turn.__str__()  # TODO incomplete


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
    time_limit = models.DateTimeField(blank=True, null=True)  # TODO: use this
    round_time_limit = models.DateTimeField(blank=True, null=True)  # TODO: use this

    def latest_turn(self):
        return Turn.objects.filter(match=self).order_by('-number').first()

    def join_player(self, player):
        if self.status != self.STATUS_SETUP:
            raise MatchInWrongStatus()
        if self.players.count() >= self.map.num_seats:
            raise MatchIsFull()
        if player not in Player.objects.get_match_candidates(self):
            raise PlayerCannotJoinMatch()
        MatchPlayer.objects.create_player(self, player)

    def match_player_ready(self, match_player):
        if self.status not in (self.STATUS_PAUSED, self.STATUS_PLAYING, self.STATUS_SETUP):
            raise MatchInWrongStatus()
        if self.map.num_seats == self.players.count():
            all_ready = True
            for player in self.players.all():
                if not player.setup_ready:
                    all_ready = False
            if all_ready:
                self.all_players_ready()

    def all_players_ready(self):
        if self.status == self.STATUS_SETUP:
            self.transition_from_setup_to_playing()
        elif self.status == self.STATUS_PLAYING:
            self.process_turn()
        elif self.status == self.STATUS_PAUSED:
            pass
        else:
            raise MatchInWrongStatus()

    def transition_from_setup_to_playing(self):
        # Create first turn
        turn = Turn.objects.create(match=self, number=1)
        turn.save()

        # Assign countries to players and assign starting tokens
        countries = list(self.map.countries.all())
        players = list(self.players.all())
        for i in range(self.players.all().count()):
            player = players[i]
            player.country = countries[i]
            player.save()

            player_in_turn = PlayerInTurn(turn=turn, match_player=player, power_points=0, flag_controlled_by=player)
            player_in_turn.save()

            starting_tokens = (
                (2, BoardTokenType.objects.get(name="Infantry")),
                (2, BoardTokenType.objects.get(name="Small Tank")),
                (2, BoardTokenType.objects.get(name="Fighter")),
                (2, BoardTokenType.objects.get(name="Destroyer")),
            )
            for token_tuples in starting_tokens:
                for j in range(token_tuples[0]):
                    BoardToken(owner=player_in_turn, position=player.country.reserve, type=token_tuples[1]).save()

            player_in_turn.calculate_total_strength()
            player_in_turn.save()

        self.status = self.STATUS_PLAYING
        self.save()

    def process_turn(self):
        pass
        # TODO Process movements
        # TODO tokens only one move per round, except from reserve
        # TODO cannot move to same tile except missiles
        # TODO if no valid movements, substract power point
        # TODO Process battles
        # TODO Calculate forces
        # TODO Winner: capture (Missiles don't capture, infinite strength missiles destroy power points)
        # TODO Draw: retreat, recurse
        #TODO Collect power points, one per country with flag
        #TODO Flag capture (including tokens and power points)
        # TODO Check victory

    def get_absolute_url(self):
        return reverse('game.views.view_match', kwargs={'match_pk': self.pk})

    def __str__(self):
        return self.name


class MatchPlayerManager(models.Manager):
    def create_player(self, match, player):
        match_player = self.create(match=match, player=player)
        return match_player

    def get_by_match_and_player(self, match, player):
        try:
            return self.get(match=match, player=player)
        except MatchPlayer.DoesNotExist:
            return None


class MatchPlayer(models.Model):
    objects = MatchPlayerManager()

    match = models.ForeignKey(Match, related_name='players')
    player = models.ForeignKey(Player, related_name='match_players')
    setup_ready = models.BooleanField(default=False)
    country = models.ForeignKey(MapCountry, related_name='players', blank=True, null=True)
    timeout_requested = models.BooleanField(default=False)  # TODO: use this
    left_match = models.BooleanField(default=False)  # TODO: use this
    defeated = models.BooleanField(default=False)  # TODO: use this

    def latest_player_in_turn(self):
        return PlayerInTurn.objects.filter(match_player=self).order_by('-turn_id').first()

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
        if self.match.status == Match.STATUS_SETUP:
            if self.setup_ready:
                raise MatchPlayerAlreadyReady
            self.setup_ready = True
            self.save()
            self.match.match_player_ready(self)
        elif self.match.status in (Match.STATUS_PLAYING, Match.STATUS_PAUSED):
            self.latest_player_in_turn().make_ready()
        else:
            raise MatchInWrongStatus()


    def __str__(self):
        return '%s in %s' % (self.player.user.username, self.match.name)

