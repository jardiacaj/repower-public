from django.core.urlresolvers import reverse
from django.test import TestCase

from account.models import Player
from account.tests import create_test_users, create_inactive_players
from game.models import Match, MatchPlayer, Turn, PlayerInTurn, BoardToken, Command, BoardTokenType, MapRegion





# TODO: test map view


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

        # Log in alice
        response = self.client.post(reverse('account.views.login'),
                                    data={'username': 'alicemail@localhost', 'password': 'apwd'}, follow=True)
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
        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.login'),
                                    data={'username': players[1], 'password': 'bpwd'}, follow=True)
        self.assertRedirects(response, reverse('game.views.start'))
        self.assertIn('_auth_user_id', self.client.session)

        # Make ready
        response = self.client.get(reverse('game.views.ready', kwargs={'match_pk': match.pk}), follow=True)
        self.assertRedirects(response, match.get_absolute_url())
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[0]).setup_ready)
        self.assertTrue(MatchPlayer.objects.get_by_match_and_player(match, players[1]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[3]).setup_ready)
        self.assertFalse(MatchPlayer.objects.get_by_match_and_player(match, players[4]).setup_ready)
        self.assertEqual(match.status, Match.STATUS_SETUP)

        # Logout and login as player 4
        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.login'),
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
        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.login'),
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

    def test_start_two_player_game(self):
        players = create_test_users()
        inactive_players = create_inactive_players()

        # Login
        response = self.client.post(reverse('account.views.login'),
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
        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.login'),
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
        self.assertContains(response, "This token type cannot be purchased")
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
        response = self.client.post(reverse('account.views.logout'), follow=True)
        self.assertRedirects(response, reverse('account.views.login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('account.views.login'),
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

        # TODO: make ready & trigger turn 2
        # TODO: when another map available, try movements to other map's locations
        # TODO: try adding commands when not playing

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
        self.assertRedirects(response, match.get_absolute_url())

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
        self.assertRedirects(response, match.get_absolute_url())

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
        self.assertRedirects(response, match.get_absolute_url())
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
        self.assertRedirects(response, match.get_absolute_url())


        # TODO    def test_join_public_private(self):
        # TODO test creating match with private map