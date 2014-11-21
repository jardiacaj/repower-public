from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.core.urlresolvers import reverse

from game.models import Match, MatchPlayer, Turn, PlayerInTurn, BoardToken, Command, BoardTokenType, MapRegion, Player, \
    Invite


def create_test_users():
    user = User.objects.create_user('Alice', 'alicemail@localhost', 'apwd')
    player = Player(user=user)
    player.save()
    player_two = Player.objects.create_player('bobmail@localhost', 'Bob', 'bpwd')
    player_three = Player.objects.create_player('carolmail@localhost', 'Carol', 'cpwd')
    player_four = Player.objects.create_player('davemail@localhost', 'Dave', 'dpwd')
    player_five = Player.objects.create_player('evemail@localhost', 'Eve', 'epwd')
    return [player, player_two, player_three, player_four, player_five]


def create_not_player():
    return User.objects.create_user('noplayer@localhost', 'noplayer@localhost', 'apwd')


def create_inactive_players():
    player_one = Player.objects.create_player('Inactive', 'inactive1@localhost', 'ipwd')
    player_one.user.is_active = False
    player_one.user.save()
    player_two = Player.objects.create_player('InactiveTwo', 'inactive2@localhost', 'ipwd')
    player_two.user.is_active = False
    player_two.user.save()
    return [player_one, player_two]


class AccessTests(TestCase):
    def test_get_start_page(self):
        response = self.client.post(reverse('game.views.home'))
        self.assertEqual(response.status_code, 200)

    def test_get_login_page(self):
        response = self.client.post(reverse('game.views.login'))
        self.assertEqual(response.status_code, 200)


class LoginTests(TestCase):
    def test_invalid_user(self):
        response = self.client.post(reverse('game.views.login'), data={'username': 'test', 'password': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_pass(self):
        create_test_users()
        response = self.client.post(
            reverse('game.views.login'),
            data={'username': 'alicemail@localhost', 'password': 'wrong'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inactive_user(self):
        players = create_inactive_players()
        response = self.client.post(
            reverse('game.views.login'),
            data={'username': players[0].user.username, 'password': 'ipwd'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, 'This account is inactive')

    def test_user_but_not_player_login(self):
        user = create_not_player()
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, "is not a player")

    def test_valid_login(self):
        create_test_users()
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': 'Alice', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_valid_login_and_logout(self):
        create_test_users()
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': 'Alice', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.login'), follow=True)
        self.assertRedirects(response, reverse('game.views.start'))

        response = self.client.get(reverse('game.views.home'))
        self.assertRedirects(response, reverse('game.views.start'))

        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)


class InviteTests(TestCase):
    @skipIf(settings.SKIP_MAIL_TESTS, "Mail test")
    def test_send_invite(self):
        create_test_users()
        create_not_player()
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': 'Alice', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'joan.ardiaca@gmail.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has been sent")
        self.assertTrue(Invite.objects.filter(email="joan.ardiaca@gmail.com").exists())

        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'joan.ardiaca@gmail.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "was already invited")

        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'noplayer@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You cannot invite this player")
        self.assertFalse(Invite.objects.filter(email="noplayer@localhost").exists())

        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'invalidmail'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "has been sent")
        self.assertFalse(Invite.objects.filter(email="invalidmail").exists())

        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'test1@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has been sent")
        self.assertTrue(Invite.objects.filter(email="test1@localhost").exists())

        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'test1@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "was already invited")

        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'test2@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has been sent")
        self.assertTrue(Invite.objects.filter(email="test2@localhost").exists())

        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'test3@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You used up all your invites")
        self.assertFalse(Invite.objects.filter(email="test3@localhost").exists())

    @skipIf(settings.SKIP_MAIL_TESTS, "Mail test")
    def test_send_and_accept_invite(self):
        create_test_users()

        # Log in
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': 'Alice', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Send invite
        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'test1@localhost'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'has been sent')

        invite = Invite.objects.get(email='test1@localhost')
        self.assertIsNotNone(invite)
        self.assertEqual(invite.invitor, Player.objects.get_by_user(User.objects.get(email='alicemail@localhost')))
        self.assertTrue(invite.valid)
        self.assertEqual(len(invite.code), settings.INVITE_CODE_LENGTH)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(invite.get_absolute_url(), mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, settings.INVITE_MAIL_SENDER_ADDRESS)
        self.assertEqual(mail.outbox[0].to, [invite.email])

        # Log out
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        # Wrong respond invite page
        response = self.client.get(reverse('game.views.respond_game_invite', kwargs={'code': 'fakecode'}))
        self.assertEqual(response.status_code, 404)

        # Respond invite page
        response = self.client.get(invite.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        # Post without post-data
        response = self.client.post(
            invite.get_absolute_url()
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "field is required")
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        # Post without password
        response = self.client.post(
            invite.get_absolute_url(),
            data={'username': 'blub'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "field is required")
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        # Post without password confirmation
        response = self.client.post(
            invite.get_absolute_url(),
            data={'username': 'blub', 'password': 'badpwd'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "field is required")
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        # Post with wrong password confirmation
        response = self.client.post(
            invite.get_absolute_url(),
            data={'username': 'blub', 'password': 'badpwd', 'password_confirm': 'very_bad_pwd'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your passwords do not match")
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        # Post without username
        response = self.client.post(
            invite.get_absolute_url(),
            data={'password': 'good_pwd', 'password_confirm': 'good_pwd'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "field is required")
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        # Post already existing username
        response = self.client.post(
            invite.get_absolute_url(),
            data={'username': 'Alice', 'password': 'good_pwd', 'password_confirm': 'good_pwd'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This user name is alredy taken.")
        self.assertFalse(User.objects.filter(email='test1@localhost').exists())

        # Post correctly
        response = self.client.post(
            invite.get_absolute_url(),
            data={'username': 'blub', 'password': 'good_pwd', 'password_confirm': 'good_pwd'},
            follow=True
        )
        self.assertRedirects(response, reverse('game.views.home'))
        self.assertContains(response, "Please log in")
        self.assertTrue(User.objects.filter(email='test1@localhost').exists())
        self.assertTrue(User.objects.filter(username='blub').exists())
        self.assertTrue(Player.objects.get_by_user(User.objects.get(email='test1@localhost')))

        # Try to reuse invite
        response = self.client.get(invite.get_absolute_url(), follow=True)
        self.assertRedirects(response, reverse('game.views.home'))
        self.assertContains(response, "This invite cannot be used")

        response = self.client.post(
            invite.get_absolute_url(),
            data={'username': 'blub2', 'password': 'good_pwd', 'password_confirm': 'good_pwd'},
            follow=True
        )
        self.assertRedirects(response, reverse('game.views.home'))
        self.assertContains(response, "This invite cannot be used")

        # Log in
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': 'blub', 'password': 'good_pwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Log out
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        # Log in
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': 'Alice', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)
        self.assertContains(response, "1 notifications")

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 notifications")
        self.assertContains(response, "NEW")
        self.assertContains(response, "joined Repower")


class UnauthenticatedAccess(TestCase):
    def test_game_invite_no_login(self):
        response = self.client.post(reverse('game.views.game_invite'), data={'email': 'test1@localhost'}, follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_game_start_no_login(self):
        response = self.client.get(reverse('game.views.start'), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_notifications_no_login(self):
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_new_match_no_login(self):
        response = self.client.get(reverse('game.views.new_match'), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_public_matches_no_login(self):
        response = self.client.get(reverse('game.views.public_matches'), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_view_match_no_login(self):
        response = self.client.get(reverse('game.views.view_match', kwargs={'match_pk': 1}), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_match_invite_no_login(self):
        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': 1}), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_match_invite_player_no_login(self):
        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': 1, 'player_pk': 1}),
                                   follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_ready_no_login(self):
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': 1}), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_leave_match_no_login(self):
        response = self.client.get(reverse('game.views.leave', kwargs={'match_pk': 1}), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_make_public_no_login(self):
        response = self.client.get(reverse('game.views.make_public', kwargs={'match_pk': 1}), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_make_private_no_login(self):
        response = self.client.get(reverse('game.views.make_private', kwargs={'match_pk': 1}), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_kick_no_login(self):
        response = self.client.get(reverse('game.views.kick', kwargs={'match_pk': 1, 'player_pk': 1}), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_add_command_no_login(self):
        response = self.client.get(reverse('game.views.add_command', kwargs={'match_pk': 1}), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_delete_command_no_login(self):
        response = self.client.get(reverse('game.views.delete_command', kwargs={'match_pk': 1, 'order': 0}),
                                   follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_view_map_in_match_no_login(self):
        response = self.client.get(reverse('game.views.view_map_in_match', kwargs={'match_pk': 1}), follow=True)
        self.assertContains(response, "Welcome to Repower")


class ViewCallsTests(TestCase):
    def test_view_map(self):
        response = self.client.get(reverse('game.views.view_map', kwargs={'map_pk': 1}))
        self.assertEqual(response.status_code, 200)

    def test_view_token(self):
        tokens = BoardTokenType.objects.all()
        for token in tokens:
            response = self.client.get(reverse('game.views.view_token', kwargs={'token_type_pk': token.id}))
            self.assertEqual(response.status_code, 200)


class MatchPlay(TestCase):
    def test_start_four_player_game(self):
        players = create_test_users()
        inactive_players = create_inactive_players()

        # Log in alice
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': 'Alice', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Create match
        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '2'},
                                    follow=True)
        match = Match.objects.get(pk=1)
        self.assertTrue(match)
        self.assertEqual(match.owner, players[0])
        self.assertEqual(match.players.count(), 1)
        self.assertEqual(match.players.get().player, players[0])
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, players[0].user.username)

        # Go back home
        response = self.client.get(reverse('game.views.start'))
        self.assertContains(response, 'testmatch')

        # Invite page
        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        self.assertNotIn(players[0], Player.objects.get_match_candidates(match))
        self.assertIn(players[1], Player.objects.get_match_candidates(match))
        self.assertIn(players[2], Player.objects.get_match_candidates(match))
        self.assertIn(players[3], Player.objects.get_match_candidates(match))
        self.assertIn(players[4], Player.objects.get_match_candidates(match))
        self.assertNotIn(inactive_players[0], Player.objects.get_match_candidates(match))
        self.assertNotIn(inactive_players[1], Player.objects.get_match_candidates(match))

        # Invite inactive player
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': inactive_players[1].pk}),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(match.players.count(), 1)
        self.assertContains(response, "This player can not be invited")
        self.assertContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        self.assertNotIn(players[0], Player.objects.get_match_candidates(match))
        self.assertIn(players[1], Player.objects.get_match_candidates(match))
        self.assertIn(players[2], Player.objects.get_match_candidates(match))
        self.assertIn(players[3], Player.objects.get_match_candidates(match))
        self.assertIn(players[4], Player.objects.get_match_candidates(match))
        self.assertNotIn(inactive_players[0], Player.objects.get_match_candidates(match))
        self.assertNotIn(inactive_players[1], Player.objects.get_match_candidates(match))

        # Invite player 1
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertEqual(match.players.count(), 2)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertNotContains(response, players[3].user.username)
        self.assertNotContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        # Back to invite page
        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)

        self.assertNotIn(players[0], Player.objects.get_match_candidates(match))
        self.assertNotIn(players[1], Player.objects.get_match_candidates(match))
        self.assertIn(players[2], Player.objects.get_match_candidates(match))
        self.assertIn(players[3], Player.objects.get_match_candidates(match))
        self.assertIn(players[4], Player.objects.get_match_candidates(match))

        # Invite player 4
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[4].pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertEqual(match.players.count(), 3)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertNotContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)

        # Try to invite again
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[4].pk}), follow=True)
        self.assertRedirects(response, reverse('game.views.match_invite', kwargs={'match_pk': match.id}))
        self.assertEqual(match.players.count(), 3)
        self.assertContains(response, "This player can not be invited")
        self.assertNotContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertNotContains(response, players[4].user.username)

        self.assertNotIn(players[0], Player.objects.get_match_candidates(match))
        self.assertNotIn(players[1], Player.objects.get_match_candidates(match))
        self.assertIn(players[2], Player.objects.get_match_candidates(match))
        self.assertIn(players[3], Player.objects.get_match_candidates(match))
        self.assertNotIn(players[4], Player.objects.get_match_candidates(match))

        # Back to invite page
        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertNotContains(response, players[4].user.username)

        self.assertNotIn(players[0], Player.objects.get_match_candidates(match))
        self.assertNotIn(players[1], Player.objects.get_match_candidates(match))
        self.assertIn(players[2], Player.objects.get_match_candidates(match))
        self.assertIn(players[3], Player.objects.get_match_candidates(match))
        self.assertNotIn(players[4], Player.objects.get_match_candidates(match))

        # Invite player 3
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[3].pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertEqual(match.players.count(), 4)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)

        # Invite player 2
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[2].pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertEqual(match.players.count(), 4)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertContains(response, "Match is full")

        # Make game public, then private again
        response = self.client.get(reverse('game.views.make_public', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(Match.objects.get(pk=match.pk).public)

        response = self.client.get(reverse('game.views.make_private', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertFalse(Match.objects.get(pk=match.pk).public)

        # Make player 0 ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[3]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[4]).setup_ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        # Logout and login as player 1
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 notifications")
        self.assertContains(response, "NEW")
        self.assertContains(response, "invited you to play")

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).setup_ready)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[3]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[4]).setup_ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        # Logout and login as player 4
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[4], 'password': 'epwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).setup_ready)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[3]).setup_ready)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[4]).setup_ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        # Logout and login as player 3
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[3], 'password': 'dpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Make ready (starting the match)
        # TODO: cannot continue without 4 player map
        """
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[0]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[3]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[4]).setup_ready)
        match = Match.objects.get(pk=match.pk)
        self.assertEqual(match.status, Match.STATUS_PLAYING)
        """

    def test_play_two_player_game(self):  # TODO: make smaller tests
        players = create_test_users()
        inactive_players = create_inactive_players()

        # Login
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0].user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Create match
        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '1'},
                                    follow=True)
        match = Match.objects.get(pk=1)
        self.assertTrue(match)
        self.assertEqual(match.owner, players[0])
        self.assertEqual(match.players.count(), 1)
        self.assertEqual(match.players.get().player, players[0])
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, players[0].user.username)

        response = self.client.get(reverse('game.views.start'))
        self.assertContains(response, 'testmatch')

        # Invite page
        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        self.assertNotIn(players[0], Player.objects.get_match_candidates(match))
        self.assertIn(players[1], Player.objects.get_match_candidates(match))
        self.assertIn(players[2], Player.objects.get_match_candidates(match))
        self.assertIn(players[3], Player.objects.get_match_candidates(match))
        self.assertIn(players[4], Player.objects.get_match_candidates(match))
        self.assertNotIn(inactive_players[0], Player.objects.get_match_candidates(match))
        self.assertNotIn(inactive_players[1], Player.objects.get_match_candidates(match))

        # Invite inactive player
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': inactive_players[1].pk}),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(match.players.count(), 1)
        self.assertContains(response, "This player can not be invited")
        self.assertContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        self.assertNotIn(players[0], Player.objects.get_match_candidates(match))
        self.assertIn(players[1], Player.objects.get_match_candidates(match))
        self.assertIn(players[2], Player.objects.get_match_candidates(match))
        self.assertIn(players[3], Player.objects.get_match_candidates(match))
        self.assertIn(players[4], Player.objects.get_match_candidates(match))
        self.assertNotIn(inactive_players[0], Player.objects.get_match_candidates(match))
        self.assertNotIn(inactive_players[1], Player.objects.get_match_candidates(match))

        # Invite self, player 0
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[0].pk}), follow=True)
        self.assertRedirects(response, reverse('game.views.match_invite', kwargs={'match_pk': match.id}))
        self.assertEqual(match.players.count(), 1)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        # Invite player 1
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertEqual(match.players.count(), 2)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertNotContains(response, players[3].user.username)
        self.assertNotContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        # Back to invite page
        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)

        self.assertNotIn(players[0], Player.objects.get_match_candidates(match))
        self.assertNotIn(players[1], Player.objects.get_match_candidates(match))
        self.assertIn(players[2], Player.objects.get_match_candidates(match))
        self.assertIn(players[3], Player.objects.get_match_candidates(match))
        self.assertIn(players[4], Player.objects.get_match_candidates(match))

        # Invite self to full game
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[0].pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertEqual(match.players.count(), 2)
        self.assertContains(response, "Match is full")

        # Make public and private again
        response = self.client.get(reverse('game.views.make_public', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(Match.objects.get(pk=match.pk).public)

        response = self.client.get(reverse('game.views.make_private', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertFalse(Match.objects.get(pk=match.pk).public)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).setup_ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        # Logout and login as player 1
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Make ready, starting the game
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).setup_ready)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).setup_ready)
        match = Match.objects.get(pk=match.pk)
        self.assertEqual(match.status, Match.STATUS_PLAYING)
        countries = list(match.map.countries.all())
        self.assertEqual(MatchPlayer.objects.get_by_match_and_player(match, players[0]).country, countries[0])
        self.assertEqual(MatchPlayer.objects.get_by_match_and_player(match, players[1]).country, countries[1])
        turn = Turn.objects.get(match=match, number=1)
        self.assertEqual(len(PlayerInTurn.objects.filter(match_player__match=match)), 2)
        self.assertEqual(len(BoardToken.objects.filter(
            owner__match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]))), 8)
        self.assertEqual(len(BoardToken.objects.filter(
            owner__match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]))), 8)
        self.assertEqual(PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0])).total_strength, 40)
        self.assertEqual(PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1])).total_strength, 40)

        # Try to add invalid commands
        self.assertEqual(Command.objects.all().count(), 0)

        # Using get instead of post
        response = self.client.get(reverse('game.views.add_command', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Post me a command")
        self.assertEqual(Command.objects.all().count(), 0)

        # No post data
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid command type")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid command type
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'LOL'}, follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid command type")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid movement, no parameters
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'move'}, follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid token type")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid movement, no regions set
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'move', 'move_token_type': 1}, follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid location(s)")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid movement, missing destination
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'move', 'move_token_type': 1, 'move_region_from': 1},
                                    follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid location(s)")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid movement, missing source
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'move', 'move_token_type': 1, 'move_region_to': 1},
                                    follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid location(s)")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid movement, missing token
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'move', 'move_region_from': 1, 'move_region_to': 1},
                                    follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid token type")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid purchase, missing token type
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'buy'},
                                    follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid token type")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid purchase, non-purchasable token
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'buy',
                                          'buy_token_type': BoardTokenType.objects.filter(
                                              purchasable=False).first().pk},
                                    follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid token type")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid conversion, missing parameters
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'convert'},
                                    follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid conversion")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid conversion, missing location
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'convert', 'convert_id': 1},
                                    follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid location")
        self.assertEqual(Command.objects.all().count(), 0)

        # Invalid conversion, missing conversion
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={'command_type': 'convert', 'convert_region': 1},
                                    follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, "Invalid conversion")
        self.assertEqual(Command.objects.all().count(), 0)

        # Logout and login as player 2
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[2], 'password': 'cpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Try to add command (but is not a player)
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={
                                        'command_type': 'move',
                                        'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                                        'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                                        'move_region_to': MapRegion.objects.get(name="South HQ").id},
                                    follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertEqual(Command.objects.all().count(), 0)
        self.assertContains(response, "You are not playing in this match")
        self.assertContains(response, "You can not see this match")

        # Try to delete command (but is not a player)
        response = self.client.get(reverse('game.views.delete_command', kwargs={'match_pk': match.pk, 'order': 0}),
                                   follow=True)
        self.assertContains(response, "You are not playing in this match")
        self.assertEqual(Command.objects.all().count(), 0)

        # Try to view match (but it's private and not a player)
        response = self.client.get(reverse('game.views.view_match', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertContains(response, "You can not see this match")

        response = self.client.get(reverse('game.views.view_map_in_match', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertContains(response, "You can not see this match")

        # Logout and login as player 1
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Add, then delete commands
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'buy',
                               'buy_token_type': BoardTokenType.objects.get(name="Small Tank").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 1)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'buy',
                               'buy_token_type': BoardTokenType.objects.get(name="Small Tank").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 2)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'buy',
                               'buy_token_type': BoardTokenType.objects.get(name="Small Tank").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 3)

        response = self.client.get(reverse('game.views.delete_command', kwargs={'match_pk': match.pk, 'order': 1}),
                                   follow=True)
        self.assertContains(response, "Command deleted")
        self.assertEqual(Command.objects.all().count(), 2)

        response = self.client.get(reverse('game.views.delete_command', kwargs={'match_pk': match.pk, 'order': 1}),
                                   follow=True)
        self.assertContains(response, "Command deleted")
        self.assertEqual(Command.objects.all().count(), 1)

        response = self.client.get(reverse('game.views.delete_command', kwargs={'match_pk': match.pk, 'order': 1}),
                                   follow=True)
        self.assertContains(response, "Invalid command")
        self.assertEqual(Command.objects.all().count(), 1)

        response = self.client.get(reverse('game.views.delete_command', kwargs={'match_pk': match.pk, 'order': 0}),
                                   follow=True)
        self.assertContains(response, "Command deleted")
        self.assertEqual(Command.objects.all().count(), 0)

        # Player 1 movements in turn 1:
        # Small tank from reserve to headquarters
        # Small tank from headquarters to South 5
        # Small tank from South 5 to South 8 (won't work)
        # Purchase infantry (won't work)
        # Convert 3 infantry to regiment in South Reserve (won't work)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="South HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 1)

        command = Command.objects.first()
        self.assertEqual(command.order, 0)
        self.assertEqual(command.type, Command.TYPE_MOVEMENT)
        self.assertIsNone(command.valid)
        self.assertIsNone(command.conversion)
        self.assertEqual(command.location, MapRegion.objects.get(name="South Reserve"))
        self.assertEqual(command.move_destination, MapRegion.objects.get(name="South HQ"))
        self.assertEqual(command.player_in_turn,
                         MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn())
        self.assertEqual(command.token_type, BoardTokenType.objects.get(name="Small Tank"))
        self.assertIsNone(command.value_conversion)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="South HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 5").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 2)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="South 5").id,
                             'move_region_to': MapRegion.objects.get(name="South 8").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 3)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'buy',
                               'buy_token_type': BoardTokenType.objects.get(name="Small Tank").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 4)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'convert',
                               'convert_id': 1,
                               'convert_region': MapRegion.objects.get(name="South Reserve").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 5)

        # Try to add 6th movement
        response = self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                                    data={
                                        'command_type': 'move',
                                        'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                                        'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                                        'move_region_to': MapRegion.objects.get(name="South HQ").id},
                                    follow=True)
        self.assertEqual(Command.objects.all().count(), 5)
        self.assertContains(response, "You can not add more commands this turn")

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn().ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[0]).latest_player_in_turn().ready)

        # Logout and login as player 0
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0], 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Player 0 movements in turn 1:
        # Fighter from reserve to headquarters
        # Fighter from reserve to headquarters
        # Fighter from reserve to headquarters (won't work)
        # Fighter from headquarters to South 7
        # Fighter from headquarters to South 8 (won't work)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 6)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 7)
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 8)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 9)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 8").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 10)

        # Make ready, triggering turn 2
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())

        players_in_turn = dict()
        players_in_turn[1] = dict()
        players_in_turn[1][0] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]),
            turn__number=1
        )
        players_in_turn[1][1] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]),
            turn__number=1
        )
        players_in_turn[2] = dict()
        players_in_turn[2][0] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]),
            turn__number=2
        )
        players_in_turn[2][1] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]),
            turn__number=2
        )

        valid_commands = (0, 1)
        for command in Command.objects.filter(player_in_turn=players_in_turn[1][1]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)

        valid_commands = (0, 1, 3)
        for command in Command.objects.filter(player_in_turn=players_in_turn[1][0]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)

        # Board status end of turn 1:
        # Player 0:
        # 1 power point
        # 1 fighter in South 7
        # 1 fighter in North HQ
        #   2 infantry, 2 small tanks, 2 destroyers in reserve
        # Player 1:
        #   0 power points
        #   1 small tank in South 5
        #   2 infantry, 1 small tank, 2 fighters, 2 destroyers in reserve

        self.assertTrue(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South 7"),
            owner=players_in_turn[2][0]
        ).exists())
        self.assertTrue(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="North HQ"),
            owner=players_in_turn[2][0]
        ).exists())
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="North Reserve"),
            owner=players_in_turn[2][0]
        ).count(), 6)
        self.assertTrue(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Small Tank"),
            position=MapRegion.objects.get(name="South 5"),
            owner=players_in_turn[2][1]
        ).exists())
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[2][1]
        ).count(), 7)

        self.assertEqual(players_in_turn[2][0].power_points, 1)
        self.assertEqual(players_in_turn[2][1].power_points, 0)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 notifications")
        self.assertContains(response, "NEW")
        self.assertContains(response, "New turn")

        # Player 0 movements in turn 2:
        # Fighter from headquarters to South 7
        # Fighter from headquarters to South 7 (won't work)
        # Destroyer from reserve to headquarters
        # Destroyer from headquarters to North 4 (won't work)
        # Destroyer from headquarters to North 1
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 11)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 12)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Destroyer").id,
                             'move_region_from': MapRegion.objects.get(name="North Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 13)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Destroyer").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="North 4").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 14)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Destroyer").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="North 1").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 15)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).latest_player_in_turn().ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn().ready)

        # Logout and login as player 1
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 notifications")
        self.assertContains(response, "NEW")
        self.assertContains(response, "New turn")
        self.assertContains(response, "invited you to play")

        # Player 1 movements in turn 2:
        # Small Tank from South 5 to North 9 (won't work)
        # Small Tank from South 5 to Ocean 9 (won't work)
        # Small Tank from South 5 to South reserve (won't work)
        # Small Tank from South 5 to West Island
        # Fighter from South Reserve to South 2 (won't work)
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="South 5").id,
                             'move_region_to': MapRegion.objects.get(name="North 9").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 16)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="South 5").id,
                             'move_region_to': MapRegion.objects.get(name="Ocean 9").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 17)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="South 5").id,
                             'move_region_to': MapRegion.objects.get(name="South Reserve").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 18)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="South 5").id,
                             'move_region_to': MapRegion.objects.get(name="West Island").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 19)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="South 2").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 20)

        # Make ready, triggering turn 3
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())

        players_in_turn = dict()
        players_in_turn[3] = dict()
        players_in_turn[3][0] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]),
            turn__number=3
        )
        players_in_turn[3][1] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]),
            turn__number=3
        )

        players_in_turn[2] = dict()
        valid_commands = (0, 2, 4)
        for command in Command.objects.filter(player_in_turn=players_in_turn[3][0]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)

        valid_commands = (3,)
        for command in Command.objects.filter(player_in_turn=players_in_turn[3][1]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)


        # Board status end of turn 2:
        # Player 0:
        #   2 power points
        #   2 fighters in South 7
        #   1 destroyer in North 1
        #   2 infantry, 2 small tanks, 1 destroyer in reserve
        # Player 1:
        #   0 power points
        #   1 small tank in West Island
        #   2 infantry, 1 small tank, 2 fighters, 2 destroyers in reserve

        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South 7"),
            owner=players_in_turn[3][0]
        ).count(), 2)
        self.assertTrue(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="North 1"),
            owner=players_in_turn[3][0]
        ).exists())
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="North Reserve"),
            owner=players_in_turn[3][0]
        ).count(), 5)
        self.assertTrue(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Small Tank"),
            position=MapRegion.objects.get(name="West Island"),
            owner=players_in_turn[3][1]
        ).exists())
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[3][1]
        ).count(), 7)
        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[3][0]).count(), 8)
        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[3][1]).count(), 8)

        self.assertEqual(players_in_turn[3][0].power_points, 2)
        self.assertEqual(players_in_turn[3][1].power_points, 0)

        # Player 1 movements in turn 3:
        # Fighter from South Reserve to South HQ
        # Fighter from South Reserve to South HQ
        # Fighter from South HQ to South 7
        # Fighter from South HQ to South 7
        # Small Tank from West Island to North HQ (won't work)
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="South HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 21)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="South HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 22)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 23)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 24)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="West Island").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 25)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn().ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[0]).latest_player_in_turn().ready)

        # Logout and login as player 0
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0], 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Player 0 movements in turn 3:
        # Buy fighter (won't work)
        # Buy Small Tank (won't work)
        # Buy Infantry
        # Convert 3 Infantry to Regiment
        # Move Regiment from North Reserve to North HQ
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'buy',
                               'buy_token_type': BoardTokenType.objects.get(name="Fighter").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 26)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'buy',
                               'buy_token_type': BoardTokenType.objects.get(name="Small Tank").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 27)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'buy',
                               'buy_token_type': BoardTokenType.objects.get(name="Infantry").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 28)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'convert',
                               'convert_id': 1,
                               'convert_region': MapRegion.objects.get(name="North Reserve").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 29)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Regiment").id,
                             'move_region_from': MapRegion.objects.get(name="North Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 30)

        # Make ready, triggering turn 4
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())

        players_in_turn[4] = dict()
        players_in_turn[4][0] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]),
            turn__number=4
        )
        players_in_turn[4][1] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]),
            turn__number=4
        )

        valid_commands = (2, 3, 4)
        for command in Command.objects.filter(player_in_turn=players_in_turn[3][0]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)

        valid_commands = (0, 1, 2, 3)
        for command in Command.objects.filter(player_in_turn=players_in_turn[3][1]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)

        # Board status end of turn 3:
        # Player 0:
        #   1 power points
        #   2 fighters in South 7
        #   1 destroyer in North 1
        #   1 regiment in North HQ
        #   2 small tanks, 1 destroyer in reserve
        # Player 1:
        #   0 power points
        #   1 small tank in West Island
        #   2 Fighters in South HQ (retreated from South 7)
        #   2 infantry, 1 small tank, 2 destroyers in reserve

        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South 7"),
            owner=players_in_turn[4][0]
        ).count(), 2)
        self.assertTrue(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="North 1"),
            owner=players_in_turn[4][0]
        ).exists())
        self.assertTrue(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Regiment"),
            position=MapRegion.objects.get(name="North HQ"),
            owner=players_in_turn[4][0]
        ).exists())
        self.assertFalse(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="North Reserve"),
            owner=players_in_turn[4][0]
        ).exists())
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="North Reserve"),
            owner=players_in_turn[4][0]
        ).count(), 3)
        self.assertTrue(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Small Tank"),
            position=MapRegion.objects.get(name="West Island"),
            owner=players_in_turn[4][1]
        ).exists())
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South HQ"),
            owner=players_in_turn[4][1]
        ).count(), 2)
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[4][1]
        ).count(), 5)
        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[4][0]).count(), 7)
        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[4][1]).count(), 8)

        self.assertEqual(players_in_turn[4][0].power_points, 1)
        self.assertEqual(players_in_turn[4][1].power_points, 0)

        # Player 0 movements in turn 4:
        # Move Regiment from North HQ to North 6
        # Move Destroyer from North 1 to North 5 (won't work)
        # Move Destroyer from North 1 to Ocean 1
        # Move Fighter from South 7 to South 3
        # Move Fighter from South 7 to Ocean 9 (won't work)
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Regiment").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="North 6").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 31)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Destroyer").id,
                             'move_region_from': MapRegion.objects.get(name="North 1").id,
                             'move_region_to': MapRegion.objects.get(name="North 5").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 32)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Destroyer").id,
                             'move_region_from': MapRegion.objects.get(name="North 1").id,
                             'move_region_to': MapRegion.objects.get(name="Ocean 1").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 33)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South 7").id,
                             'move_region_to': MapRegion.objects.get(name="South 3").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 34)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South 7").id,
                             'move_region_to': MapRegion.objects.get(name="Ocean 9").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 35)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).latest_player_in_turn().ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn().ready)

        # Logout and login as player 1
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Player 1 movements in turn 4:
        # Move small tank from West Island to North 6
        # Move Fighter from South HQ to South 7
        # Move Fighter from South HQ to South 7
        # Move Infantry from South Reserve to South HQ
        # Move Infantry from South Reserve to South HQ
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="West Island").id,
                             'move_region_to': MapRegion.objects.get(name="North 6").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 36)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 37)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 38)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="South HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 39)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="South HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 40)

        # Make ready, triggering turn 5
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())

        players_in_turn[5] = dict()
        players_in_turn[5][0] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]),
            turn__number=5
        )
        players_in_turn[5][1] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]),
            turn__number=5
        )

        valid_commands = (0, 2, 3)
        for command in Command.objects.filter(player_in_turn=players_in_turn[4][0]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)

        valid_commands = (0, 1, 2, 3, 4)
        for command in Command.objects.filter(player_in_turn=players_in_turn[4][1]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)

        # Board status end of turn 4:
        # Player 0:
        #   2 power points
        #   1 fighter in South 7 DEFEATED!
        #   1 fighter in South 3
        #   1 destroyer in Ocean 1
        #   1 regiment in North 6
        #   3 small tanks (1 from capture), 1 destroyer in reserve
        # Player 1:
        #   0 power points
        #   1 small tank in North 6 DEFEATED!
        #   2 Fighters in South 7
        #   2 Infantry in HQ
        #   1 small tank, 2 destroyers, 1 fighter from capture in reserve
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South 7"),
            owner=players_in_turn[5][0]
        ).count(), 0)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South 3"),
            owner=players_in_turn[5][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="Ocean 1"),
            owner=players_in_turn[5][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Regiment"),
            position=MapRegion.objects.get(name="North 6"),
            owner=players_in_turn[5][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Small Tank"),
            owner=players_in_turn[5][0]
        ).count(), 3)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Small Tank"),
            position=MapRegion.objects.get(name="North Reserve"),
            owner=players_in_turn[5][0]
        ).count(), 3)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="North Reserve"),
            owner=players_in_turn[5][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Small Tank"),
            position=MapRegion.objects.get(name="North 6"),
            owner=players_in_turn[5][1]
        ).count(), 0)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Small Tank"),
            owner=players_in_turn[5][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South 7"),
            owner=players_in_turn[5][1]
        ).count(), 2)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="South HQ"),
            owner=players_in_turn[5][1]
        ).count(), 2)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Small Tank"),
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[5][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[5][1]
        ).count(), 2)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[5][1]
        ).count(), 1)

        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[5][0]).count(), 7)
        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[5][1]).count(), 8)

        self.assertEqual(players_in_turn[5][0].power_points, 2)
        self.assertEqual(players_in_turn[5][1].power_points, 0)

        # Player 1 movements in turn 5:
        # Move Fighter from South 7 to North HQ
        # Move Fighter from South 7 to North 7
        # Move Fighter from South Reserve to South HQ
        # Move Infantry from South HQ to South 4
        # Move Infantry from South HQ to South 4
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South 7").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 41)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South 7").id,
                             'move_region_to': MapRegion.objects.get(name="North 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 42)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="South HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 43)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="South HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 4").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 44)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="South HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 4").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 45)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn().ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[0]).latest_player_in_turn().ready)

        # Logout and login as player 0
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0], 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Player 0 movements in turn 5:
        # Move Small Tank from North Reserve to North HQ
        # Move Small Tank from North Reserve to North HQ
        # Move Small Tank from North Reserve to North HQ
        # Convert 3 small tanks to tank in North HQ
        # Move Tank from North HQ to North 2 (won't work)
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="North Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 46)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="North Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 47)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Small Tank").id,
                             'move_region_from': MapRegion.objects.get(name="North Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 48)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={'command_type': 'convert',
                               'convert_id': 2,
                               'convert_region': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 49)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Tank").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="North 2").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 50)

        # Make ready, triggering turn 6
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())

        players_in_turn[6] = dict()
        players_in_turn[6][0] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]),
            turn__number=6
        )
        players_in_turn[6][1] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]),
            turn__number=6
        )

        valid_commands = (0, 1, 2, 3)
        for command in Command.objects.filter(player_in_turn=players_in_turn[5][0]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)

        valid_commands = (0, 1, 2, 3, 4)
        for command in Command.objects.filter(player_in_turn=players_in_turn[5][1]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)

        # Board status end of turn 5:
        # Player 0:
        #   3 power points
        #   1 Tank in North HQ
        #   1 fighter in South 3
        #   1 destroyer in Ocean 1
        #   1 regiment in North 6
        #   1 destroyer, 1 fighter from capture in reserve
        # Player 1:
        #   1 power points
        #   1 Fighters in North HQ DEFEATED!
        #   1 Fighters in North 7
        #   1 Fighters in South HQ
        #   2 Infantry in South 4
        #   1 small tank, 2 destroyers in reserve
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Tank"),
            position=MapRegion.objects.get(name="North HQ"),
            owner=players_in_turn[6][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South 3"),
            owner=players_in_turn[6][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="Ocean 1"),
            owner=players_in_turn[6][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Regiment"),
            position=MapRegion.objects.get(name="North 6"),
            owner=players_in_turn[6][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="North Reserve"),
            owner=players_in_turn[6][0]
        ).count(), 2)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="North 7"),
            owner=players_in_turn[6][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South HQ"),
            owner=players_in_turn[6][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="South 4"),
            owner=players_in_turn[6][1]
        ).count(), 2)
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[6][1]
        ).count(), 3)

        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[6][0]).count(), 6)
        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[6][1]).count(), 7)

        self.assertEqual(players_in_turn[6][0].power_points, 3)
        self.assertEqual(players_in_turn[6][1].power_points, 1)

        # Player 0 movements in turn 6:
        # Move Fighter from South 3 to South 6 (will revert from draw)
        # Move Tank from North HQ to North 8
        # Move Destroyer from Ocean 1 to East Island
        # Move Regiment from North 6 to North 9
        # Move Fighter from North Reserve to North HQ
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South 3").id,
                             'move_region_to': MapRegion.objects.get(name="South 6").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 51)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Tank").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="North 8").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 52)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Destroyer").id,
                             'move_region_from': MapRegion.objects.get(name="Ocean 1").id,
                             'move_region_to': MapRegion.objects.get(name="East Island").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 53)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Regiment").id,
                             'move_region_from': MapRegion.objects.get(name="North 6").id,
                             'move_region_to': MapRegion.objects.get(name="North 9").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 54)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 55)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).latest_player_in_turn().ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn().ready)

        # Logout and login as player 1
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Player 1 movements in turn 6:
        # Move Fighter from South HQ to South 6 (will revert from draw)
        # Move Fighter from North 7 to South 3 (will revert from draw)
        # Move Infantry from South 4 to West Island
        # Move Infantry from South 4 to South 7
        # Move Destroyer from South Reserve to North HQ (won't work)
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 6").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 56)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North 7").id,
                             'move_region_to': MapRegion.objects.get(name="South 3").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 57)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="South 4").id,
                             'move_region_to': MapRegion.objects.get(name="West Island").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 58)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="South 4").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 59)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Destroyer").id,
                             'move_region_from': MapRegion.objects.get(name="South Reserve").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 60)

        # Make ready, triggering turn 7
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())

        players_in_turn[7] = dict()
        players_in_turn[7][0] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]),
            turn__number=7
        )
        players_in_turn[7][1] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]),
            turn__number=7
        )

        valid_commands = (0, 1, 2, 3, 4)
        reverted_commands = (0, )
        for command in Command.objects.filter(player_in_turn=players_in_turn[6][0]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)
            self.assertEqual(command.reverted_in_draw, command.order in reverted_commands,
                             "Command #%d" % command.order)

        valid_commands = (0, 1, 2, 3)
        reverted_commands = (0, 1)
        for command in Command.objects.filter(player_in_turn=players_in_turn[6][1]):
            self.assertEqual(command.valid, command.order in valid_commands, "Command #%d" % command.order)
            self.assertEqual(command.reverted_in_draw, command.order in reverted_commands,
                             "Command #%d" % command.order)

        # Board status end of turn 6
        # Player 0:
        #   4 power points
        #   1 Tank in North 8
        #   1 fighter in South 3 (retreated)
        #   1 destroyer in East Island
        #   1 regiment in North 9
        #   1 fighter in North HQ
        #   1 destroyer in reserve
        # Player 1:
        #   2 power points
        #   1 Fighters in North 7 (retreated)
        #   1 Fighters in South HQ (retreated)
        #   1 Infantry in West Island
        #   1 Infantry in South 7
        #   1 small tank, 2 destroyers in reserve
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Tank"),
            position=MapRegion.objects.get(name="North 8"),
            owner=players_in_turn[7][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South 3"),
            owner=players_in_turn[7][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="East Island"),
            owner=players_in_turn[7][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Regiment"),
            position=MapRegion.objects.get(name="North 9"),
            owner=players_in_turn[7][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="North HQ"),
            owner=players_in_turn[7][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="North Reserve"),
            owner=players_in_turn[7][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="North 7"),
            owner=players_in_turn[7][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South HQ"),
            owner=players_in_turn[7][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="West Island"),
            owner=players_in_turn[7][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="South 7"),
            owner=players_in_turn[7][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[7][1]
        ).count(), 3)

        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[7][0]).count(), 6)
        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[7][1]).count(), 7)

        self.assertEqual(players_in_turn[7][0].power_points, 4)
        self.assertEqual(players_in_turn[7][1].power_points, 2)

        # Player 1 commands in turn 7:
        # Move Fighter from South HQ to North 8 (won't work)
        # Move Infantry from South 7 to to North 9 (won't work)
        # Move Infantry from West Island to North 5
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="South HQ").id,
                             'move_region_to': MapRegion.objects.get(name="North 8").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 61)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="South 7").id,
                             'move_region_to': MapRegion.objects.get(name="North 9").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 62)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="West Island").id,
                             'move_region_to': MapRegion.objects.get(name="North 5").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 63)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn().ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[0]).latest_player_in_turn().ready)

        # Logout and login as player 0
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0], 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Player 0 movements in turn 7:
        # Move Tank from North 8 to South 8 (won't work)
        # Move Tank from North 8 to South 7 (won't work)
        # Move Tank from North 8 to South 9 (won't work)
        # Move Regiment from North 9 to South 7 (won't work)
        # Move Destroyer from East Island to South 6 (won't work)
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Tank").id,
                             'move_region_from': MapRegion.objects.get(name="North 8").id,
                             'move_region_to': MapRegion.objects.get(name="South 8").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 64)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Tank").id,
                             'move_region_from': MapRegion.objects.get(name="North 8").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 65)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Tank").id,
                             'move_region_from': MapRegion.objects.get(name="North 8").id,
                             'move_region_to': MapRegion.objects.get(name="South 9").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 66)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Regiment").id,
                             'move_region_from': MapRegion.objects.get(name="North 9").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 67)

        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Destroyer").id,
                             'move_region_from': MapRegion.objects.get(name="East Island").id,
                             'move_region_to': MapRegion.objects.get(name="South 6").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 68)

        # Make ready, triggering turn 8
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())

        players_in_turn[8] = dict()
        players_in_turn[8][0] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]),
            turn__number=8
        )
        players_in_turn[8][1] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]),
            turn__number=8
        )

        for command in Command.objects.filter(player_in_turn=players_in_turn[7][0]):
            self.assertFalse(command.valid, "Command #%d" % command.order)

        for command in Command.objects.filter(player_in_turn=players_in_turn[7][1]):
            self.assertEqual(command.valid, command.order == 2, "Command #%d" % command.order)

        # Board status end of turn 7
        # Player 0:
        #   4 power points (no increase because no valid movements)
        #   1 Tank in North 8
        #   1 fighter in South 3 (retreated)
        #   1 destroyer in East Island
        #   1 regiment in North 9
        #   1 fighter in North HQ
        #   1 destroyer in reserve
        # Player 1:
        #   3 power points
        #   1 Fighters in North 7
        #   1 Fighters in South HQ
        #   1 Infantry in North 5
        #   1 Infantry in South 7
        #   1 small tank, 2 destroyers in reserve
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Tank"),
            position=MapRegion.objects.get(name="North 8"),
            owner=players_in_turn[8][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South 3"),
            owner=players_in_turn[8][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="East Island"),
            owner=players_in_turn[8][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Regiment"),
            position=MapRegion.objects.get(name="North 9"),
            owner=players_in_turn[8][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="North HQ"),
            owner=players_in_turn[8][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="North Reserve"),
            owner=players_in_turn[8][0]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="North 7"),
            owner=players_in_turn[8][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South HQ"),
            owner=players_in_turn[8][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="North 5"),
            owner=players_in_turn[8][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="South 7"),
            owner=players_in_turn[8][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[8][1]
        ).count(), 3)

        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[8][0]).count(), 6)
        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[8][1]).count(), 7)

        self.assertEqual(players_in_turn[8][0].power_points, 4)
        self.assertEqual(players_in_turn[8][1].power_points, 3)

        # Player 0 movements in turn 8
        # Move Fighter from North HQ to South 7
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Fighter").id,
                             'move_region_from': MapRegion.objects.get(name="North HQ").id,
                             'move_region_to': MapRegion.objects.get(name="South 7").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 69)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).latest_player_in_turn().ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn().ready)

        # Logout and login as player 1
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Player 1 movements in turn 8
        # Move Infantry from North 5 to North HQ
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="North 5").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 70)

        # Make ready, triggering turn 9 and ending the game
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())

        players_in_turn[9] = dict()
        players_in_turn[9][0] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]),
            turn__number=9
        )
        players_in_turn[9][1] = PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]),
            turn__number=9
        )

        for command in Command.objects.filter(player_in_turn=players_in_turn[8][0]):
            self.assertTrue(command.valid, "Command #%d" % command.order)

        for command in Command.objects.filter(player_in_turn=players_in_turn[8][1]):
            self.assertTrue(command.valid, "Command #%d" % command.order)

        # Board status end of turn 8
        # Player 0: DEFEATED
        #   0 power points
        # Player 1:
        #   8 power points
        #   1 Fighters in North 7
        #   1 Fighters in South HQ
        #   1 Infantry in North HQ
        #   1 small tank, 4 destroyers, 1 Tank, 2 Fighter, 1 Regiment, 1 Infantry in reserve
        self.assertEqual(BoardToken.objects.filter(
            owner=players_in_turn[9][0]
        ).count(), 0)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="North 7"),
            owner=players_in_turn[9][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South HQ"),
            owner=players_in_turn[9][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="North HQ"),
            owner=players_in_turn[9][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="South 7"),
            owner=players_in_turn[9][1]
        ).count(), 0)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Small Tank"),
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[9][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Destroyer"),
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[9][1]
        ).count(), 4)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Tank"),
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[9][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Fighter"),
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[9][1]
        ).count(), 2)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Regiment"),
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[9][1]
        ).count(), 1)
        self.assertEqual(BoardToken.objects.filter(
            type=BoardTokenType.objects.get(name="Infantry"),
            position=MapRegion.objects.get(name="South Reserve"),
            owner=players_in_turn[9][1]
        ).count(), 1)

        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[9][0]).count(), 0)
        self.assertEqual(BoardToken.objects.filter(owner=players_in_turn[9][1]).count(), 13)

        self.assertEqual(players_in_turn[9][0].power_points, 0)
        self.assertEqual(players_in_turn[9][1].power_points, 7)

        self.assertTrue(players_in_turn[9][0].defeated)
        self.assertFalse(players_in_turn[9][1].defeated)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).latest_player_in_turn().defeated)
        self.assertFalse(
            MatchPlayer.objects.get_by_match_and_player(match, players[1]).latest_player_in_turn().defeated)
        match = Match.objects.get(id=match.id)
        self.assertEqual(match.status, Match.STATUS_FINISHED)

        # Try to add command after game end
        self.client.post(reverse('game.views.add_command', kwargs={'match_pk': match.pk}),
                         data={
                             'command_type': 'move',
                             'move_token_type': BoardTokenType.objects.get(name="Infantry").id,
                             'move_region_from': MapRegion.objects.get(name="North 5").id,
                             'move_region_to': MapRegion.objects.get(name="North HQ").id},
                         follow=True)
        self.assertEqual(Command.objects.all().count(), 70)

        # Try to delete command after game end
        response = self.client.get(reverse('game.views.delete_command', kwargs={'match_pk': match.pk, 'order': 0}),
                                   follow=True)
        self.assertContains(response, "You can not delete commands this turn")
        self.assertEqual(Command.objects.all().count(), 70)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 notifications")
        self.assertContains(response, "NEW")
        self.assertContains(response, "Congratulations")

        # Logout and login as player 0
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0], 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 notifications")
        self.assertContains(response, "NEW")
        self.assertContains(response, "You lost")

        # TODO: when another map available, try movements to other map's locations

    def test_kicks(self):
        players = create_test_users()

        # Login as player 0
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0].user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Create match
        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '1'},
                                    follow=True)
        match = Match.objects.get(pk=1)
        self.assertTrue(match)

        # Invite player 1
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)

        # Kick player 1
        response = self.client.get(
            reverse('game.views.kick', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 1)
        self.assertRedirects(response, match.get_absolute_url())

        # Invite player 1
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)

        # Logout and login as player 1
        response = self.client.get(reverse('game.views.logout'), follow=True)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 notifications")
        self.assertContains(response, "NEW")
        self.assertContains(response, "You have been kicked from")

        # Try to kick self
        response = self.client.get(
            reverse('game.views.kick', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)
        self.assertRedirects(response, match.get_absolute_url())

        # Try to kick owner
        response = self.client.get(
            reverse('game.views.kick', kwargs={'match_pk': match.pk, 'player_pk': players[0].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)
        self.assertRedirects(response, match.get_absolute_url())


    def test_leave_during_setup(self):
        players = create_test_users()

        # Log in a player 0
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0].user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Create new match
        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '1'},
                                    follow=True)
        match = Match.objects.get(pk=1)
        self.assertTrue(match)

        # Invite player 1
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)

        # Leave match, aborting it (player is owner)
        response = self.client.get(reverse('game.views.leave', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        match = Match.objects.get(pk=1)
        self.assertEqual(match.players.count(), 2)
        self.assertEqual(match.status, Match.STATUS_SETUP_ABORTED)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NEW")
        self.assertContains(response, "has been aborted because the owner")

        # Create match
        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '1'},
                                    follow=True)
        match = Match.objects.get(pk=2)
        self.assertTrue(match)

        # Invite player 1
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)

        # Log out and log in as player 1
        response = self.client.get(reverse('game.views.logout'), follow=True)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NEW")
        self.assertContains(response, "has been aborted because the owner")

        # Leave match
        response = self.client.get(reverse('game.views.leave', kwargs={'match_pk': match.pk}), follow=True)
        match = Match.objects.get(pk=2)
        self.assertEqual(match.players.count(), 1)
        self.assertEqual(match.status, Match.STATUS_SETUP)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertContains(response, "0 notifications")

        # Log out and log in as player 0
        response = self.client.get(reverse('game.views.logout'), follow=True)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0], 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NEW")
        self.assertContains(response, "%s left from %s" % (players[1].user.username, match.name))

    def test_leave_on_first_turn_two_players(self):
        players = create_test_users()
        inactive_players = create_inactive_players()

        # Login
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0].user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Create match
        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '1'},
                                    follow=True)
        match = Match.objects.get(pk=1)
        self.assertTrue(match)
        self.assertEqual(match.owner, players[0])
        self.assertEqual(match.players.count(), 1)
        self.assertEqual(match.players.get().player, players[0])
        self.assertRedirects(response, match.get_absolute_url())
        self.assertContains(response, players[0].user.username)

        response = self.client.get(reverse('game.views.start'))
        self.assertContains(response, 'testmatch')

        # Invite player 1
        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertEqual(match.players.count(), 2)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertNotContains(response, players[3].user.username)
        self.assertNotContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).setup_ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        # Logout and login as player 1
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Make ready, starting the game
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).setup_ready)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).setup_ready)
        match = Match.objects.get(pk=match.pk)
        self.assertEqual(match.status, Match.STATUS_PLAYING)
        countries = list(match.map.countries.all())
        self.assertEqual(MatchPlayer.objects.get_by_match_and_player(match, players[0]).country, countries[0])
        self.assertEqual(MatchPlayer.objects.get_by_match_and_player(match, players[1]).country, countries[1])
        turn = Turn.objects.get(match=match, number=1)
        self.assertEqual(len(PlayerInTurn.objects.filter(match_player__match=match)), 2)
        self.assertEqual(len(BoardToken.objects.filter(
            owner__match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0]))), 8)
        self.assertEqual(len(BoardToken.objects.filter(
            owner__match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1]))), 8)
        self.assertEqual(PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[0])).total_strength, 40)
        self.assertEqual(PlayerInTurn.objects.get(
            match_player=MatchPlayer.objects.get_by_match_and_player(match, players[1])).total_strength, 40)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NEW")
        self.assertContains(response, "started!")

        # Leave game
        response = self.client.get(reverse('game.views.leave', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        match = Match.objects.get(pk=1)
        self.assertEqual(match.players.count(), 2)
        self.assertEqual(match.status, Match.STATUS_FINISHED)
        match_player = dict()
        match_player[0] = MatchPlayer.objects.get_by_match_and_player(match, players[0])
        match_player[1] = MatchPlayer.objects.get_by_match_and_player(match, players[1])
        self.assertFalse(match_player[0].left_match)
        self.assertFalse(match_player[0].latest_player_in_turn().left_match)
        self.assertTrue(match_player[0].is_active())
        self.assertTrue(match_player[1].left_match)
        self.assertTrue(match_player[1].latest_player_in_turn().left_match)
        self.assertFalse(match_player[1].is_active())
        self.assertTrue(BoardToken.objects.filter(owner=match_player[0].latest_player_in_turn()).exists())
        self.assertFalse(BoardToken.objects.filter(owner=match_player[1].latest_player_in_turn()).exists())

        # Logout and login as player 0
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0], 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Load notifications page
        response = self.client.get(reverse('game.views.notifications'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NEW")
        self.assertContains(response, "%s left %s" % (players[1].user.username, match.name))
        self.assertContains(response, "Congratulations")
        self.assertContains(response, "started!")


class MatchListing(TestCase):
    def test_create_and_list_game(self):
        players = create_test_users()

        # Login
        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[0].user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Create private match
        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'privmatch', 'map': '1'},
                                    follow=True)
        match_private = Match.objects.get(pk=1)
        self.assertTrue(match_private)
        self.assertEqual(match_private.owner, players[0])
        self.assertEqual(match_private.players.count(), 1)
        self.assertEqual(match_private.players.get().player, players[0])
        self.assertRedirects(response, match_private.get_absolute_url())
        self.assertContains(response, players[0].user.username)

        response = self.client.get(reverse('game.views.start'))
        self.assertContains(response, match_private.name)

        # Create public match
        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'pubmatch', 'map': '1'},
                                    follow=True)
        match_public = Match.objects.get(pk=2)
        self.assertTrue(match_public)
        self.assertEqual(match_public.owner, players[0])
        self.assertEqual(match_public.players.count(), 1)
        self.assertEqual(match_public.players.get().player, players[0])
        self.assertRedirects(response, match_public.get_absolute_url())
        self.assertContains(response, players[0].user.username)

        response = self.client.get(reverse('game.views.start'))
        self.assertContains(response, match_public.name)

        # Make match public
        response = self.client.get(reverse('game.views.make_public', kwargs={'match_pk': match_public.pk}), follow=True)
        self.assertRedirects(response, match_public.get_absolute_url())
        self.assertTrue(Match.objects.get(pk=match_public.pk).public)

        # Test match listing
        response = self.client.get(reverse('game.views.public_matches'), follow=True)
        self.assertNotContains(response, match_private.name)
        self.assertContains(response, match_public.name)

        response = self.client.get(reverse('game.views.public_matches'), {'filter': 'joinable'}, follow=True)
        self.assertNotContains(response, match_private.name)
        self.assertContains(response, match_public.name)

        response = self.client.get(reverse('game.views.public_matches'), {'filter': 'all'}, follow=True)
        self.assertNotContains(response, match_private.name)
        self.assertContains(response, match_public.name)

        # Logout and login as player 1
        response = self.client.post(reverse('game.views.logout'), follow=True)
        self.assertRedirects(response, reverse('game.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('game.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Test seeing private match
        response = self.client.get(match_private.get_absolute_url(), follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertContains(response, "You can not see this match")

        # Test seeing public match
        response = self.client.get(match_public.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "You can not see this match")

        # Test invite to private match
        response = self.client.get(reverse('game.views.match_invite',
                                           kwargs={'match_pk': match_private.id, 'player_pk': players[1].pk}),
                                   follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertContains(response, "Only the owner can invite in private games")
        self.assertContains(response, "You can not see this match")

        # Test invite to public match
        response = self.client.get(reverse('game.views.match_invite',
                                           kwargs={'match_pk': match_public.id, 'player_pk': players[1].pk}),
                                   follow=True)
        self.assertRedirects(response, match_public.get_absolute_url())
        self.assertEqual(MatchPlayer.objects.count(), 3)
        self.assertNotContains(response, "Only the owner can invite in private games")
        self.assertNotContains(response, "You can not see this match")

        # TODO test creating match with private map