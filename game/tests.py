from django.core.urlresolvers import reverse
from django.test import TestCase

from account.tests import create_test_users, create_inactive_players
from game.models import Match, MatchPlayer


class UnauthenticatedAccess(TestCase):
    def test_game_start_no_login(self):
        response = self.client.get(reverse('game.views.start'), follow=True)
        self.assertContains(response, "Welcome to Repower")

    def test_new_match_no_login(self):
        response = self.client.get(reverse('game.views.new_match'), follow=True)
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


class BasicMatchSetup(TestCase):
    def test_start_four_player_game(self):
        players = create_test_users()
        inactive_players = create_inactive_players()

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': 'alicemail@localhost', 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '2'},
                                    follow=True)
        match = Match.objects.get(pk=1)
        self.assertTrue(match)
        self.assertEqual(match.owner, players[0])
        self.assertEqual(match.players.count(), 1)
        self.assertEqual(match.players.get().player, players[0])
        self.assertRedirects(response, match.url())
        self.assertContains(response, players[0].user.username)

        response = self.client.get(reverse('game.views.start'))
        self.assertContains(response, 'testmatch')

        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': inactive_players[1].pk}),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(match.players.count(), 1)
        self.assertContains(response, "This player can not be invited")
        self.assertNotContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertEqual(match.players.count(), 2)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertNotContains(response, players[3].user.username)
        self.assertNotContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, players[0].user.username)
        self.assertNotContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[4].pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertEqual(match.players.count(), 3)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertNotContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[4].pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(match.players.count(), 3)
        self.assertContains(response, "This player can not be invited")
        self.assertNotContains(response, players[0].user.username)
        self.assertNotContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertNotContains(response, players[4].user.username)

        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, players[0].user.username)
        self.assertNotContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertNotContains(response, players[4].user.username)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[3].pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertEqual(match.players.count(), 4)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[2].pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertEqual(match.players.count(), 4)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertContains(response, "Match is full")

        response = self.client.get(reverse('game.views.make_public', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertTrue(Match.objects.get(pk=match.pk).public)

        response = self.client.get(reverse('game.views.make_private', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertFalse(Match.objects.get(pk=match.pk).public)

        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[3]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[4]).ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).ready)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[3]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[4]).ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[4], 'password': 'epwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).ready)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[3]).ready)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[4]).ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[3], 'password': 'dpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[0]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[3]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[4]).ready)
        match = Match.objects.get(pk=match.pk)
        self.assertEqual(match.status, Match.STATUS_PLAYING)

    def test_start_two_player_game(self):
        players = create_test_users()
        inactive_players = create_inactive_players()

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[0].user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '1'},
                                    follow=True)
        match = Match.objects.get(pk=1)
        self.assertTrue(match)
        self.assertEqual(match.owner, players[0])
        self.assertEqual(match.players.count(), 1)
        self.assertEqual(match.players.get().player, players[0])
        self.assertRedirects(response, match.url())
        self.assertContains(response, players[0].user.username)

        response = self.client.get(reverse('game.views.start'))
        self.assertContains(response, 'testmatch')

        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': inactive_players[1].pk}),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(match.players.count(), 1)
        self.assertContains(response, "This player can not be invited")
        self.assertNotContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertEqual(match.players.count(), 2)
        self.assertContains(response, players[0].user.username)
        self.assertContains(response, players[1].user.username)
        self.assertNotContains(response, players[2].user.username)
        self.assertNotContains(response, players[3].user.username)
        self.assertNotContains(response, players[4].user.username)
        self.assertNotContains(response, inactive_players[0].user.username)
        self.assertNotContains(response, inactive_players[1].user.username)

        response = self.client.get(reverse('game.views.match_invite', kwargs={'match_pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, players[0].user.username)
        self.assertNotContains(response, players[1].user.username)
        self.assertContains(response, players[2].user.username)
        self.assertContains(response, players[3].user.username)
        self.assertContains(response, players[4].user.username)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[0].pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertEqual(match.players.count(), 2)
        self.assertContains(response, "Match is full")

        response = self.client.get(reverse('game.views.make_public', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertTrue(Match.objects.get(pk=match.pk).public)

        response = self.client.get(reverse('game.views.make_private', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertFalse(Match.objects.get(pk=match.pk).public)

        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[0]).ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[1]).ready)
        match = Match.objects.get(pk=match.pk)
        self.assertEqual(match.status, Match.STATUS_PLAYING)

    def test_kicks(self):
        players = create_test_users()

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[0].user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '1'},
                                    follow=True)
        match = Match.objects.get(pk=1)
        self.assertTrue(match)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)

        response = self.client.get(
            reverse('game.views.kick', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 1)
        self.assertRedirects(response, match.url())

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)

        response = self.client.get(reverse('account.views.logout'), follow=True)

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(
            reverse('game.views.kick', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)
        self.assertRedirects(response, match.url())

    def test_leave_during_setup(self):
        players = create_test_users()

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[0].user.username, 'password': 'apwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.new_match'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '1'},
                                    follow=True)
        match = Match.objects.get(pk=1)
        self.assertTrue(match)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)

        response = self.client.get(reverse('game.views.leave', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.url())
        match = Match.objects.get(pk=1)
        self.assertEqual(match.players.count(), 2)
        self.assertEqual(match.status, Match.STATUS_SETUP_ABORTED)

        response = self.client.post(reverse('game.views.new_match'), data={'name': 'testmatch', 'map': '1'},
                                    follow=True)
        match = Match.objects.get(pk=2)
        self.assertTrue(match)

        response = self.client.get(
            reverse('game.views.match_invite', kwargs={'match_pk': match.pk, 'player_pk': players[1].pk}), follow=True)
        self.assertEqual(match.players.count(), 2)

        response = self.client.get(reverse('account.views.logout'), follow=True)

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('game.views.leave', kwargs={'match_pk': match.pk}), follow=True)
        match = Match.objects.get(pk=2)
        self.assertEqual(match.players.count(), 1)
        self.assertEqual(match.status, Match.STATUS_SETUP)
        self.assertRedirects(response, match.url())


        # TODO    def test_join_public_private(self):