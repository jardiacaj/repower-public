from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.core.urlresolvers import reverse

from account.models import Player, Invite


def create_test_users():
    user = User.objects.create_user('alicemail@localhost', 'alicemail@localhost', 'apwd')
    player = Player(user=user)
    player.save()
    player_two = Player.objects.create_player('bobmail@localhost', 'bpwd')
    player_three = Player.objects.create_player('carolmail@localhost', 'cpwd')
    player_four = Player.objects.create_player('davemail@localhost', 'dpwd')
    player_five = Player.objects.create_player('evemail@localhost', 'epwd')
    return [player, player_two, player_three, player_four, player_five]


def create_not_player():
    return User.objects.create_user('noplayer@localhost', 'noplayer@localhost', 'apwd')


def create_inactive_players():
    player_one = Player.objects.create_player('inactive1@localhost', 'ipwd')
    player_one.user.is_active = False
    player_one.user.save()
    player_two = Player.objects.create_player('inactive2@localhost', 'ipwd')
    player_two.user.is_active = False
    player_two.user.save()
    return [player_one, player_two]


class AccessTests(TestCase):
    def test_get_start_page(self):
        response = self.client.post(reverse('Repower.views.home'))
        self.assertEqual(response.status_code, 200)

    def test_get_login_page(self):
        response = self.client.post(reverse('account.views.login'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_invite_post(self):
        response = self.client.post(reverse('account.views.invite'), data={'email': 'test1@localhost'}, follow=True)
        self.assertContains(response, "Welcome to Repower")


class LoginTests(TestCase):
    def test_invalid_user(self):
        response = self.client.post(reverse('account.views.login'), data={'username': 'test', 'password': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_pass(self):
        create_test_users()
        response = self.client.post(
            reverse('account.views.login'),
            data={'username': 'alicemail@localhost', 'password': 'wrong'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inactive_user(self):
        players = create_inactive_players()
        response = self.client.post(
            reverse('account.views.login'),
            data={'username': players[0].user.username, 'password': 'ipwd'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, 'This account is inactive')

    def test_user_but_not_player_login(self):
        user = create_not_player()
        response = self.client.post(reverse('account.views.login'),
                                    data={'username': user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, "is not a player")

    def test_valid_login(self):
        create_test_users()
        response = self.client.post(reverse('account.views.login'),
                                    data={'username': 'alicemail@localhost', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_valid_login_and_logout(self):
        create_test_users()
        response = self.client.post(reverse('account.views.login'),
                                    data={'username': 'alicemail@localhost', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('account.views.login'), follow=True)
        self.assertRedirects(response, reverse('game.views.start'))

        response = self.client.get(reverse('Repower.views.home'))
        self.assertRedirects(response, reverse('game.views.start'))

        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)


class InviteTests(TestCase):
    @skipIf(settings.SKIP_SLOW_TESTS, "Slow test")
    def test_send_invite(self):
        create_test_users()
        create_not_player()
        response = self.client.post(reverse('account.views.login'),
                                    data={'username': 'alicemail@localhost', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.invite'), data={'email': 'joan.ardiaca@gmail.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has been sent")
        self.assertTrue(Invite.objects.filter(email="joan.ardiaca@gmail.com").exists())

        response = self.client.post(reverse('account.views.invite'), data={'email': 'joan.ardiaca@gmail.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "was already invited")

        response = self.client.post(reverse('account.views.invite'), data={'email': 'noplayer@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You cannot invite this player")
        self.assertFalse(Invite.objects.filter(email="noplayer@localhost").exists())

        response = self.client.post(reverse('account.views.invite'), data={'email': 'invalidmail'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "has been sent")
        self.assertFalse(Invite.objects.filter(email="invalidmail").exists())

        response = self.client.post(reverse('account.views.invite'), data={'email': 'test1@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has been sent")
        self.assertTrue(Invite.objects.filter(email="test1@localhost").exists())

        response = self.client.post(reverse('account.views.invite'), data={'email': 'test1@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "was already invited")

        response = self.client.post(reverse('account.views.invite'), data={'email': 'test2@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has been sent")
        self.assertTrue(Invite.objects.filter(email="test2@localhost").exists())

        response = self.client.post(reverse('account.views.invite'), data={'email': 'test3@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You used up all your invites")
        self.assertFalse(Invite.objects.filter(email="test3@localhost").exists())

    @skipIf(settings.SKIP_SLOW_TESTS, "Slow test")
    def test_send_and_accept_invite(self):
        create_test_users()
        response = self.client.post(reverse('account.views.login'),
                                    data={'username': 'alicemail@localhost', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.invite'), data={'email': 'test1@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'has been sent')

        invite = Invite.objects.get(email='test1@localhost')
        self.assertIsNotNone(invite)
        self.assertEqual(invite.invitor, Player.objects.get_by_user(User.objects.get(email='alicemail@localhost')))
        self.assertTrue(invite.valid)
        self.assertEqual(len(invite.code), settings.INVITE_CODE_LENGTH)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(reverse('account.views.respond_invite', kwargs={'code': invite.code}), mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, settings.INVITE_MAIL_SENDER_ADDRESS)
        self.assertEqual(mail.outbox[0].to, [invite.email])

        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('account.views.respond_invite', kwargs={'code': 'fakecode'}))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('account.views.respond_invite', kwargs={'code': invite.code}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        response = self.client.post(
            reverse('account.views.respond_invite', kwargs={'code': invite.code}),
            data={'password': 'badpwd'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "field is required")
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        response = self.client.post(
            reverse('account.views.respond_invite', kwargs={'code': invite.code}),
            data={'password': 'badpwd', 'password_confirm': 'very_bad_pwd'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your passwords do not match")
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        response = self.client.post(
            reverse('account.views.respond_invite', kwargs={'code': invite.code}),
            data={'password': 'good_pwd', 'password_confirm': 'good_pwd'},
            follow=True
        )
        self.assertRedirects(response, reverse('Repower.views.home'))
        self.assertContains(response, "Please log in")
        self.assertTrue(User.objects.filter(email='test1@localhost').exists())
        self.assertTrue(Player.objects.get_by_user(User.objects.get(email='test1@localhost')))

        response = self.client.get(reverse('account.views.respond_invite', kwargs={'code': invite.code}), follow=True)
        self.assertRedirects(response, reverse('Repower.views.home'))
        self.assertContains(response, "This invite cannot be used")

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': 'test1@localhost', 'password': 'good_pwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

