import random
import string

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class PlayerManager(models.Manager):
    def create_player(self, email, password):
        user = User.objects.create_user(email, email, password)
        player = self.create(user=user)
        return player

    def get_by_user(self, user):
        return self.get(user=user)


class Player(models.Model):
    objects = PlayerManager()

    user = models.OneToOneField(User, db_index=True)

    def __str__(self):
        return self.user.username


class InviteManager(models.Manager):
    def create_invite(self, invitor, email):
        code = ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(settings.INVITE_CODE_LENGTH))
        invite = self.create(email=email, valid=True, code=code, invitor=invitor)
        return invite


class InvalidInviteError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class Invite(models.Model):
    objects = InviteManager()

    def create_player(self, password):
        if not self.valid:
            raise InvalidInviteError
        if User.objects.filter(email=self.email).exists():
            self.valid = False
            self.save()
            raise UserAlreadyExistsError

        self.valid = False
        self.save()

        return Player.objects.create_player(email=self.email, password=password)

    email = models.EmailField(unique=True, db_index=True)
    valid = models.BooleanField(default=True)
    code = models.CharField(max_length=20, db_index=True)
    invitor = models.ForeignKey(Player, db_index=True)

    def __str__(self):
        return '%s (%s)' % (self.email, self.code)