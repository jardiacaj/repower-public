from collections import defaultdict
from math import floor
import random
import string

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models


class InvalidInviteError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


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


class PlayerManager(models.Manager):
    def create_player(self, email, username, password):
        user = User.objects.create_user(username, email, password)
        player = self.create(user=user)
        return player

    def get_by_user(self, user):
        return self.get(user=user)

    def get_by_match(self, match):
        return self.filter(match_players__in=match.players)

    def get_match_candidates(self, match):
        return self.exclude(match_players__not_in=match.players.values('pk')).filter(user__is_active=True)


class Player(models.Model):
    objects = PlayerManager()

    user = models.OneToOneField(User, db_index=True)

    def add_notification(self, text, url):
        Notification.objects.create(
            player=self,
            text=text,
            url=url
        )

    def unread_notifications(self):
        return Notification.objects.filter(player=self, read=False)

    def set_all_notifications_read(self):
        Notification.objects.filter(player=self, read=False).update(read=True)

    def get_absolute_url(self):
        return reverse('game.views.view_account', kwargs={'username': self.user.username})

    def __str__(self):
        return self.user.username


class InviteManager(models.Manager):
    def create_invite(self, invitor, email):
        code = ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(settings.INVITE_CODE_LENGTH))
        invite = self.create(email=email, valid=True, code=code, invitor=invitor)
        return invite


class Invite(models.Model):
    objects = InviteManager()

    email = models.EmailField(unique=True, db_index=True)
    valid = models.BooleanField(default=True, db_index=True)
    code = models.CharField(max_length=20, db_index=True)
    invitor = models.ForeignKey(Player, db_index=True)

    def create_player(self, username, password):
        if not self.valid:
            raise InvalidInviteError
        if User.objects.filter(email=self.email).exists():
            self.valid = False
            self.save()
            raise UserAlreadyExistsError

        self.valid = False
        self.save()

        self.invitor.add_notification(
            "%s, invited by you, has joined Repower!" % username,
            self.invitor.get_absolute_url()
        )

        return Player.objects.create_player(email=self.email, username=username, password=password)

    def get_absolute_url(self):
        return reverse('game.views.respond_game_invite', kwargs={'code': self.code})

    def __str__(self):
        return '%s (%s)' % (self.email, self.code)


class Map(models.Model):
    num_seats = models.IntegerField(help_text="Number of seats of this map")
    name = models.CharField(max_length=30)
    image_file_name = models.CharField(max_length=30)
    public = models.BooleanField(default=False, help_text="Public maps can be used when players set up a new match")

    @staticmethod
    def check_map_path(token, source, destination):
        def check_path(token, source, destination, movements_left, crossed_water):
            if source == destination:
                return True
            if movements_left == 0:
                return False
            for link in source.usable_links():
                if link.crossing_water and (
                                not token.type.can_be_on_water and crossed_water and token.type.one_water_cross_per_movement):
                    pass
                else:
                    links_to = link.destination if link.source == source else link.source
                    if ((links_to.water and token.type.can_be_on_water) or (
                                links_to.land and token.type.can_be_on_land) ) and \
                            check_path(token, links_to, destination, movements_left - 1,
                                       crossed_water or link.crossing_water):
                        return True
            return False

        if source.map != destination.map:
            return False
        if token.owner.match_player.match.map != source.map:
            return False
        if destination.countries_with_this_reserve.exists() and not token.type.special_attack_reserves:
            return False
        if source == destination and not token.special_missile:
            return False
        if source.countries_with_this_reserve.exists():
            return destination.countries_with_this_headquarter.exists() and \
                   destination.countries_with_this_headquarter.first() == source.countries_with_this_reserve.first()
        return check_path(token, source, destination, token.type.movements, False)

    def image_in_match(self, turn):  # TODO: fix transparency
        map_image = self.image(False, False)
        tokens_per_region = defaultdict(lambda: 0)
        for token in BoardToken.objects.filter(owner__turn=turn):
            if not token.position.render_on_map:
                continue
            token_image = token.image()
            x = token.position.position_x + 5 + ((tokens_per_region[token.position_id] % 4) * 20)
            y = token.position.position_y + 20 + (floor(tokens_per_region[token.position_id] / 4) * 20)
            map_image.paste(token_image, (x, y))
            tokens_per_region[token.position_id] += 1
        return map_image

    def image(self, show_debug, show_links):
        from PIL import Image, ImageDraw, ImageFont

        image = Image.open('game/static/game/%s-play.png' % self.image_file_name)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        for region in self.regions.all():
            if region.render_on_map:
                if not show_debug:
                    draw.text((region.position_x + 5, region.position_y + 5), region.name, font=font, fill=(0, 0, 0))
                else:
                    text1 = "%s / %s" % (
                        region.name,
                        region.short_name,
                    )
                    text2 = "%s %s%s" % (
                        region.country.name if region.country else "-",
                        "L" if region.land else "",
                        "W" if region.water else "",
                    )
                    draw.text((region.position_x + 5, region.position_y + 5), text1, font=font, fill=(0, 0, 0))
                    draw.text((region.position_x + 5, region.position_y + 15), text2, font=font, fill=(0, 0, 0))
                if show_links:
                    for link in region.links_source.all():
                        if link.destination.render_on_map:
                            fill = 0
                            if link.crossing_water:
                                fill = 255
                            draw.line(
                                (region.position_x + region.size_x / 2,
                                 region.position_y + region.size_y / 2,
                                 link.destination.position_x + link.destination.size_x / 2,
                                 link.destination.position_y + link.destination.size_y / 2),
                                fill=fill
                            )
        del draw
        return image

    def __str__(self):
        return "%s (%d players)" % (self.name, self.num_seats)


class MapCountry(models.Model):
    class Meta:
        verbose_name_plural = "Map countries"

    map = models.ForeignKey(Map, related_name='countries')
    name = models.CharField(max_length=30)
    reserve = models.ForeignKey('MapRegion', related_name='countries_with_this_reserve', unique=True)
    headquarters = models.ForeignKey('MapRegion', related_name='countries_with_this_headquarter', unique=True)
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

    def usable_links(self):
        return self.links_source.all() | self.links_destination.exclude(unidirectional=True)

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
    class Meta:
        unique_together = (("match", "number", "step"),)

    match = models.ForeignKey('Match')
    number = models.PositiveIntegerField(db_index=True)
    step = models.PositiveSmallIntegerField(default=0, db_index=True)
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(blank=True, null=True)  # TODO Use this
    report = models.TextField(default='')

    def players(self):
        return PlayerInTurn.objects.filter(turn=self)

    def is_latest(self):
        return not self.objects.filter(match=self.match, number__gt=self.number).exists()

    def __str__(self):
        return "%d.%d in %s" % (self.number, self.step, self.match.name)


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
    can_capture_flag = models.BooleanField(default=False)

    special_missile = models.BooleanField(default=False)
    special_attack_reserves = models.BooleanField(default=False, help_text="Can attack reserves")
    special_destroys_all = models.BooleanField(default=False, help_text="Infinite strength, beats all")

    def image(self, country):
        from PIL import Image

        image = Image.open('game/static/game/%s.gif' % self.image_file_name)
        pixel_data = image.load()
        if country is not None:
            for y in range(image.size[0]):
                for x in range(image.size[1]):
                    if pixel_data[x, y] == 14:
                        pixel_data[x, y] = country.color_gif_palette
        return image

    def __str__(self):
        return self.name


class TokenConversion(models.Model):
    needs = models.ForeignKey(BoardTokenType, related_name="conversions_sourced")
    needs_quantity = models.PositiveSmallIntegerField(default=3)
    produces = models.ForeignKey(BoardTokenType, related_name="conversions_producing")
    produces_quantity = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return "%d %s to %d %s" % (self.needs_quantity, self.needs.name, self.produces_quantity, self.produces.name)


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
    defeated = models.BooleanField(default=False)
    total_strength = models.PositiveIntegerField(default=0)
    timeout_requested = models.BooleanField(default=False)
    ready = models.BooleanField(default=False)
    left_match = models.BooleanField(default=False)

    def status_box(self):
        return "☑" if self.ready else "☐"

    def is_active(self):
        return self.match_player.is_active()

    def can_add_commands(self):
        if not self.is_latest():
            return False
        elif not self.is_active():
            return False
        elif not self.match_player.match.is_in_progress():
            return False
        elif Command.objects.filter(player_in_turn=self).count() >= settings.COMMANDS_PER_TURN:
            return False
        return True

    def set_defeated(self):
        self.defeated = True
        self.save()
        self.match_player.defeated = True
        self.match_player.save()

    def check_and_process_defeat(self):
        defeater_token = BoardToken.objects.filter(owner__turn=self.turn,
                                                   type__can_capture_flag=True,
                                                   position=self.match_player.country.headquarters) \
            .exclude(owner=self).first()
        if defeater_token is not None:
            defeater = defeater_token.owner
            defeater.power_points += self.power_points
            defeater.save()
            self.power_points = 0
            self.set_defeated()
            captured_tokens = BoardToken.objects.filter(owner=self)
            captured_tokens.update(owner=defeater, position=defeater.match_player.country.reserve)
        else:
            if not BoardToken.objects.filter(owner=self).exists() and self.power_points == 0:
                self.set_defeated()

    def collect_power_points(self):
        countries = list()
        for token in BoardToken.objects.filter(owner=self).exclude(
                position__country=self.match_player.country):
            if token.position.country is not None and token.position.country not in countries:
                countries.append(token.position.country)
        self.power_points += len(countries)
        self.save()

    def tokens_in_reserve(self):
        return BoardToken.objects.filter(owner=self, position=self.match_player.country.reserve)

    def calculate_total_strength(self):
        self.total_strength = self.tokens.aggregate(Sum('type__strength'))['type__strength__sum']
        return self.total_strength

    def make_ready(self):
        if not self.match_player.match.is_in_progress():
            raise MatchInWrongStatus()
        if self.ready:
            raise MatchPlayerAlreadyReady()
        self.ready = True
        self.save()
        self.match_player.match.check_all_players_ready()

    def is_latest(self):
        return not PlayerInTurn.objects.filter(match_player=self.match_player,
                                               turn__number__gt=self.turn.number).exists()

    def leave(self):
        if not self.match_player.is_active() or not self.match_player.match.is_in_progress() or self.left_match or self.defeated:
            assert False
        self.left_match = True
        self.ready = True
        self.power_points = 0
        self.save()
        self.match_player.left_match = True
        self.match_player.save()
        self.match_player.match.check_and_process_end_of_game()
        BoardToken.objects.filter(owner=self).delete()

        for match_player in self.match_player.match.players.all():
            if match_player.is_active():
                match_player.player.add_notification(
                    "%s left %s." % (self.match_player.player.user.username, self.match_player.match.name),
                    self.match_player.match.get_absolute_url()
                )

        if self.match_player.match.is_in_progress():
            self.match_player.match.check_all_players_ready()

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

    def image(self):
        return self.type.image(self.owner.match_player.country)

    def __str__(self):
        return "%s in %s from %s" % (self.type.name, self.position.name, self.owner)


class Command(models.Model):
    class InvalidLocation(Exception):
        pass

    class TokenNotPurchasable(Exception):
        pass

    class InvalidCommandType(Exception):
        pass

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

    player_in_turn = models.ForeignKey(PlayerInTurn, related_name='commands')
    order = models.PositiveSmallIntegerField(db_index=True)
    type = models.CharField(max_length=3, choices=TYPES)
    location = models.ForeignKey(MapRegion, null=True, blank=True, related_name='+')
    token_type = models.ForeignKey(BoardTokenType, null=True, blank=True, related_name='+')
    valid = models.NullBooleanField()
    reverted_in_draw = models.BooleanField(default=False)

    move_destination = models.ForeignKey(MapRegion, null=True, blank=True, related_name='+')
    conversion = models.ForeignKey(TokenConversion, null=True, blank=True, related_name='+')
    value_conversion = models.ForeignKey(TokenConversion, null=True, blank=True, related_name='+')
    # TODO Value conversion token types

    def can_be_added(self):
        if self.type == Command.TYPE_MOVEMENT:
            if self.location.map_id != self.player_in_turn.match_player.match.map_id or \
                            self.move_destination.map_id != self.player_in_turn.match_player.match.map_id:
                raise Command.InvalidLocation()
        elif self.type == Command.TYPE_PURCHASE:
            if not self.token_type.purchasable:
                raise Command.TokenNotPurchasable()
        elif self.type == Command.TYPE_CONVERSION:
            if self.location.map_id != self.player_in_turn.match_player.match.map_id:
                raise Command.InvalidLocation()
        else:
            raise Command.InvalidCommandType()
        return True

    def is_valid(self, incoming_turn, incoming_player_in_turn):
        if self.type == Command.TYPE_MOVEMENT:
            token = BoardToken.objects.filter(owner__turn=incoming_turn,
                                              type=self.token_type,
                                              position=self.location).first()
            if token is None or not token.can_move_this_turn:
                return False
            elif not Map.check_map_path(token, self.location, self.move_destination):
                return False
            else:
                return True

        elif self.type == Command.TYPE_PURCHASE:
            if not self.token_type.purchasable:
                return False
            elif self.token_type.strength > incoming_player_in_turn.power_points:
                return False
            else:
                return True

        elif self.type == Command.TYPE_CONVERSION:
            consumable = BoardToken.objects.filter(
                owner=incoming_player_in_turn,
                type=self.conversion.needs,
                position=self.location
            ).order_by('can_move_this_turn')

            if consumable.count() < self.conversion.needs_quantity:
                return False
            else:
                return True

        else:
            raise Command.InvalidCommandType()

    def execute(self, incoming_turn, incoming_player_in_turn):
        assert self.valid

        if self.type == Command.TYPE_MOVEMENT:
            token = BoardToken.objects.filter(owner__turn=incoming_turn,
                                              type=self.token_type,
                                              position=self.location).first()
            token.position = self.move_destination
            token.moved_this_turn = True
            if self.location == incoming_player_in_turn.match_player.country.reserve and \
                            self.move_destination == incoming_player_in_turn.match_player.country.headquarters:
                token.can_move_this_turn = True
            else:
                token.can_move_this_turn = False
            token.save()

        elif self.type == Command.TYPE_PURCHASE:
            incoming_player_in_turn.power_points -= self.token_type.strength
            incoming_player_in_turn.save()
            BoardToken.objects.create(
                type=self.token_type,
                position=incoming_player_in_turn.match_player.country.reserve,
                owner=incoming_player_in_turn
            )

        elif self.type == Command.TYPE_CONVERSION:
            consumable = BoardToken.objects.filter(
                owner=incoming_player_in_turn,
                type=self.conversion.needs,
                position=self.location
            ).order_by('can_move_this_turn')

            for t in consumable[:self.conversion.needs_quantity]:
                t.delete()
            for i in range(self.conversion.produces_quantity):
                BoardToken.objects.create(
                    type=self.conversion.produces,
                    position=self.location,
                    owner=incoming_player_in_turn,
                    can_move_this_turn=
                    self.location == incoming_player_in_turn.match_player.country.reserve
                )

        else:
            raise Command.InvalidCommandType()

    def in_game_str(self):
        if self.type == self.TYPE_MOVEMENT:
            return "Move %s from %s to %s" % (self.token_type.name, self.location.name, self.move_destination.name)
        elif self.type == self.TYPE_PURCHASE:
            return "Buy %s for ⌁%d" % (self.token_type.name, self.token_type.strength)
        elif self.type == self.TYPE_CONVERSION:
            return "Convert %s in %s" % (self.conversion, self.location.name)
        raise AssertionError("Invalid command type")

    def __str__(self):
        return "%s in %s by %s" % (self.type, self.location.name, self.player_in_turn.__str__())


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
    status = models.CharField(max_length=3, choices=STATUSES, db_index=True)
    public = models.BooleanField(default=False, db_index=True)
    time_limit = models.DateTimeField(blank=True, null=True)  # TODO: use this
    round_time_limit = models.DateTimeField(blank=True, null=True)  # TODO: use this

    def is_in_progress(self):
        return self.status in (Match.STATUS_PLAYING, Match.STATUS_PAUSED)

    def has_started(self):
        return self.status in (Match.STATUS_FINISHED, Match.STATUS_ABORTED, Match.STATUS_PAUSED, Match.STATUS_PLAYING)

    def latest_turn(self):
        return Turn.objects.filter(match=self).order_by('-number').first()

    def can_view_match(self, player):
        return self.public or player in [player.player for player in self.players.all()]

    def join_player(self, player):
        if self.status != self.STATUS_SETUP:
            raise MatchInWrongStatus()
        if self.players.count() >= self.map.num_seats:
            raise MatchIsFull()
        if player not in Player.objects.get_match_candidates(self):
            raise PlayerCannotJoinMatch()
        MatchPlayer.objects.create_player(self, player)

    def check_all_players_ready(self):
        if self.status not in (self.STATUS_PAUSED, self.STATUS_PLAYING, self.STATUS_SETUP):
            raise MatchInWrongStatus()
        if self.map.num_seats == self.players.count():
            all_ready = True
            if self.status == self.STATUS_SETUP:
                for player in self.players.all():
                    if not player.setup_ready:
                        all_ready = False
            if self.is_in_progress():
                for player in self.players.all():
                    if not player.latest_player_in_turn().ready and player.is_active():
                        all_ready = False
            if all_ready:
                self.all_players_ready()

    check_all_players_ready.alters_data = True

    def all_players_ready(self):
        if self.status == self.STATUS_SETUP:
            self.transition_from_setup_to_playing()
        elif self.status == self.STATUS_PLAYING:
            self.process_turn()
        elif self.status == self.STATUS_PAUSED:
            pass
        else:
            raise MatchInWrongStatus()

    all_players_ready.alters_data = True

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

            player.player.add_notification("Match %s started!" % self.name, self.get_absolute_url())

            player_in_turn = PlayerInTurn(turn=turn, match_player=player, power_points=0)
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

    def process_battles(self, outgoing_turn, incoming_turn):
        iterations = 0
        while True:
            token_retreated = False
            for region in self.map.regions.all():
                tokens_in_region = BoardToken.objects.filter(owner__turn=incoming_turn, position=region)
                if tokens_in_region.count() > 1:
                    # Sort tokens per owner
                    tokens_per_player = defaultdict(list)
                    for token in tokens_in_region:
                        tokens_per_player[token.owner_id].append(token)
                    if len(tokens_per_player) > 1:
                        # There is a battle
                        # TODO If infinite strength token present, it wins. If missile, it kills every token (no capture)
                        # TODO: missiles do not capture!

                        # No infinite strength tokens, sort players by force
                        players_by_force = defaultdict(list)
                        for player_in_battle, tokens in tokens_per_player.items():
                            # Add up force, missiles only count if fired this turn
                            players_by_force[
                                sum(token.type.strength for token in tokens
                                    if not token.type.special_missile or
                                    (token.type.special_missile and token.move_this_turn))
                            ].append(player_in_battle)

                        winners = PlayerInTurn.objects.filter(id__in=players_by_force[max(players_by_force.keys())])

                        if len(winners) == 1:
                            # Single winner case, capture tokens
                            # TODO: missiles do not capture!
                            winner = winners[0]
                            for token in tokens_in_region:
                                if token.owner != winner:
                                    token.owner = winner
                                    token.position = winner.match_player.country.reserve
                                    token.save()
                        elif len(winners) > 1:
                            # Draw: retreat winner forces
                            for token in tokens_in_region:
                                if token.owner in winners and not token.retreat_from_draw:
                                    revertable_command = Command.objects.filter(
                                        player_in_turn__match_player=token.owner.match_player,
                                        player_in_turn__turn=outgoing_turn,
                                        valid=True,
                                        reverted_in_draw=False,
                                        type=Command.TYPE_MOVEMENT,
                                        move_destination=token.position,
                                        token_type=token.type
                                    ).first()
                                    if revertable_command is not None:
                                        revertable_command.reverted_in_draw = True
                                        revertable_command.save()
                                        token.position = revertable_command.location
                                        token.retreat_from_draw = True
                                        token.save()
                                        token_retreated = True
            if not token_retreated:
                break
            iterations += 1
            if iterations >= settings.MAX_BATTLE_ITERATIONS:
                assert False

    def check_and_process_end_of_game(self):
        remaining_players = [match_player
                             for match_player
                             in self.players.all()
                             if match_player.is_active()]
        if len(remaining_players) <= 1:
            self.status = self.STATUS_FINISHED
            for match_player in self.players.all():
                if match_player in remaining_players:
                    match_player.player.add_notification(
                        "Congratulations! You won the match %s!" % self.name,
                        self.get_absolute_url()
                    )
                elif not match_player.left_match:
                    match_player.player.add_notification(
                        "You lost the match %s" % self.name,
                        self.get_absolute_url()
                    )
        self.save()

    def process_turn(self):
        # Create new turn
        outgoing_turn = self.latest_turn()
        incoming_turn = Turn.objects.create(match=self, number=outgoing_turn.number + 1)
        incoming_turn.save()

        # Clone players
        for player in PlayerInTurn.objects.filter(turn=outgoing_turn):
            player.pk = None
            player.turn = incoming_turn
            player.ready = False
            player.save(force_insert=True)

        # Clone tokens
        for token in BoardToken.objects.filter(owner__in=PlayerInTurn.objects.filter(turn=outgoing_turn)):
            token.pk = None
            token.moved_this_turn = False
            token.can_move_this_turn = True
            token.retreat_from_draw = False
            token.owner = PlayerInTurn.objects.get(match_player=token.owner.match_player, turn=incoming_turn)
            token.save(force_insert=True)

        # Process commands
        for outgoing_player_in_turn in PlayerInTurn.objects.filter(turn=outgoing_turn):
            incoming_player_in_turn = PlayerInTurn.objects.get(turn=incoming_turn,
                                                               match_player=outgoing_player_in_turn.match_player)

            valid_command = False
            for command in outgoing_player_in_turn.commands.all().order_by('order'):
                command.valid = command.is_valid(incoming_turn, incoming_player_in_turn)
                if command.valid:
                    valid_command = True
                    command.execute(incoming_turn, incoming_player_in_turn)
                command.save()

            # if no valid movements, substract power point
            if not valid_command and incoming_player_in_turn.power_points > 0:
                incoming_player_in_turn.power_points -= 1
                incoming_player_in_turn.save()

        # Process battles
        self.process_battles(outgoing_turn, incoming_turn)

        # Delete shot missiles and steal power points from shot infinite strength missiles
        for missile in BoardToken.objects.filter(owner__turn=incoming_turn,
                                                 type__special_missile=True,
                                                 moved_this_turn=True):
            reserve_of = missile.location.countries_with_this_reserve.first()
            if missile.special_destroys_all and reserve_of:
                steal_from = PlayerInTurn.objects.filter(turn=incoming_turn, match_player__country=reserve_of)
                missile.owner.power_points += steal_from.power_points
                missile.owner.save()
                steal_from.power_points = 0
                steal_from.save()
            missile.delete()

        # Flag capture & defeats
        for match_player in (match_player for match_player in self.players.all() if not match_player.defeated):
            match_player.latest_player_in_turn().check_and_process_defeat()

        # Check end of game
        self.check_and_process_end_of_game()

        if self.is_in_progress():
            # Collect power points
            for player_in_turn in PlayerInTurn.objects.filter(turn=incoming_turn):
                player_in_turn.collect_power_points()

            # Send notifications
            for player_in_turn in PlayerInTurn.objects.filter(turn=incoming_turn):
                if player_in_turn.is_active():
                    player_in_turn.match_player.player.add_notification(
                        "New turn (%d) for match %s" % (incoming_turn.number, self.name),
                        self.get_absolute_url()
                    )

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
    left_match = models.BooleanField(default=False)
    defeated = models.BooleanField(default=False)

    def latest_player_in_turn(self):
        return PlayerInTurn.objects.filter(match_player=self).order_by('-turn_id').first()

    def is_active(self):
        return not self.defeated and not self.left_match

    def kick(self):
        if self.match.status != Match.STATUS_SETUP:
            raise MatchInWrongStatus()
        if self.match.owner == self:
            raise CannotKickOwner()
        self.delete()
        self.player.add_notification(
            "You have been kicked from %s." % self.match.name,
            self.match.get_absolute_url()
        )

    def leave(self):
        if self.match.is_in_progress():
            self.latest_player_in_turn().leave()
        elif self.match.status == Match.STATUS_SETUP:
            if self.match.owner.pk == self.pk:
                self.match.status = Match.STATUS_SETUP_ABORTED
                self.match.save()
                for match_player in self.match.players.all():
                    match_player.player.add_notification(
                        "The match %s has been aborted because the owner (%s) left." %
                        (self.match.name, self.player.user.username),
                        self.match.get_absolute_url()
                    )

            else:
                self.delete()
                for match_player in self.match.players.all():
                    match_player.player.add_notification(
                        "%s left from %s." %
                        (self.player.user.username, self.match.name),
                        self.match.get_absolute_url()
                    )
        else:
            raise MatchInWrongStatus()

    def make_ready(self):
        if self.match.status == Match.STATUS_SETUP:
            if self.setup_ready:
                raise MatchPlayerAlreadyReady
            self.setup_ready = True
            self.save()
            self.match.check_all_players_ready()
        elif self.match.is_in_progress():
            self.latest_player_in_turn().make_ready()
        else:
            raise MatchInWrongStatus()

    def status_box(self):
        if self.match.status in (Match.STATUS_ABORTED, Match.STATUS_SETUP_ABORTED, Match.STATUS_FINISHED) \
                or not self.is_active():
            return "☒"
        elif self.match.status == Match.STATUS_SETUP:
            return "☑" if self.setup_ready else "☐"
        elif self.match.is_in_progress():
            return self.latest_player_in_turn().status_box()
        assert False

    def __str__(self):
        return '%s in %s' % (self.player.user.username, self.match.name)


class Notification(models.Model):
    player = models.ForeignKey(Player)
    read = models.BooleanField(default=False, db_index=True)
    time = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length=300)
    url = models.CharField(max_length=300)

    def __str__(self):
        return "%s (to %s, %s, URL: %s)" % (self.text, self.player, "read" if self.read else "unread", self.url)