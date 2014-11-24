# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Battle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoardToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('moved_this_turn', models.BooleanField(default=False)),
                ('can_move_this_turn', models.BooleanField(default=True)),
                ('retreat_from_draw', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoardTokenType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=3)),
                ('image_file_name', models.CharField(max_length=30)),
                ('movements',
                 models.PositiveSmallIntegerField(help_text='Number of tiles this token can cross in one move')),
                ('strength', models.PositiveSmallIntegerField()),
                ('purchasable', models.BooleanField(
                    help_text='Purchasable tokens can be bought with power pointsequivalent to their strength',
                    default=False)),
                ('one_water_cross_per_movement', models.BooleanField(default=False)),
                ('can_be_on_land', models.BooleanField(default=False)),
                ('can_be_on_water', models.BooleanField(default=False)),
                ('can_capture_flag', models.BooleanField(default=False)),
                ('special_missile', models.BooleanField(default=False)),
                ('special_attack_reserves', models.BooleanField(help_text='Can attack reserves', default=False)),
                ('special_destroys_all', models.BooleanField(help_text='Infinite strength, beats all', default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Command',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('order', models.PositiveSmallIntegerField(db_index=True)),
                ('type', models.CharField(max_length=3, choices=[('MOV', 'Move'), ('TCO', 'Token conversion'),
                                                                 ('VCO', 'Value conversion'),
                                                                 ('BUY', 'Token purchase')])),
                ('valid', models.NullBooleanField()),
                ('reverted_in_draw', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('email', models.EmailField(max_length=75, unique=True, db_index=True)),
                ('valid', models.BooleanField(default=True, db_index=True)),
                ('code', models.CharField(max_length=20, unique=True, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Map',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('num_seats', models.IntegerField(help_text='Number of seats of this map')),
                ('name', models.CharField(max_length=30)),
                ('image_file_name', models.CharField(max_length=30)),
                ('public', models.BooleanField(help_text='Public maps can be used when players set up a new match',
                                               default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapCountry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30)),
                ('color_rgb', models.CharField(max_length=6)),
                ('color_gif_palette', models.PositiveSmallIntegerField()),
            ],
            options={
                'verbose_name_plural': 'Map countries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapRegion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=3)),
                ('land', models.BooleanField(default=False)),
                ('water', models.BooleanField(default=False)),
                ('render_on_map', models.BooleanField(default=True)),
                ('position_x', models.PositiveSmallIntegerField(default=0)),
                ('position_y', models.PositiveSmallIntegerField(default=0)),
                ('size_x', models.PositiveSmallIntegerField(default=0)),
                ('size_y', models.PositiveSmallIntegerField(default=0)),
                ('country', models.ForeignKey(null=True, to='game.MapCountry', blank=True)),
                ('map', models.ForeignKey(related_name='regions', to='game.Map')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapRegionLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('unidirectional', models.BooleanField(default=False)),
                ('crossing_water', models.BooleanField(default=False)),
                ('destination', models.ForeignKey(related_name='links_destination', to='game.MapRegion')),
                ('source', models.ForeignKey(related_name='links_source', to='game.MapRegion')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=50)),
                ('status', models.CharField(max_length=3,
                                            choices=[('SET', 'Set up'), ('SUA', 'Aborted (when in setup)'),
                                                     ('PLA', 'Playing'), ('PAU', 'Paused'), ('FIN', 'Finished'),
                                                     ('ABO', 'Aborted (when in progress)')], db_index=True)),
                ('public', models.BooleanField(default=False, db_index=True)),
                ('time_limit', models.DateTimeField(null=True, blank=True)),
                ('round_time_limit', models.DateTimeField(null=True, blank=True)),
                ('map', models.ForeignKey(related_name='matches', to='game.Map')),
            ],
            options={
                'verbose_name_plural': 'Matches',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MatchPlayer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('setup_ready', models.BooleanField(default=False)),
                ('timeout_requested', models.BooleanField(default=False)),
                ('left_match', models.BooleanField(default=False)),
                ('defeated', models.BooleanField(default=False)),
                ('country', models.ForeignKey(null=True, to='game.MapCountry', related_name='players', blank=True)),
                ('match', models.ForeignKey(related_name='players', to='game.Match')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('read', models.BooleanField(default=False, db_index=True)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('text', models.CharField(max_length=300)),
                ('url', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlayerInTurnStep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('power_points', models.PositiveSmallIntegerField()),
                ('defeated', models.BooleanField(default=False)),
                ('total_strength', models.PositiveIntegerField(default=0)),
                ('timeout_requested', models.BooleanField(default=False)),
                ('ready', models.BooleanField(default=False)),
                ('left_match', models.BooleanField(default=False)),
                ('match_player', models.ForeignKey(related_name='+', to='game.MatchPlayer')),
            ],
            options={
                'verbose_name_plural': 'Players in turn',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TokenConversion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('needs_quantity', models.PositiveSmallIntegerField(default=3)),
                ('produces_quantity', models.PositiveSmallIntegerField(default=1)),
                ('needs', models.ForeignKey(related_name='conversions_sourced', to='game.BoardTokenType')),
                ('produces', models.ForeignKey(related_name='conversions_producing', to='game.BoardTokenType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TokenValueConversion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('from_points', models.BooleanField(default=False)),
                ('from_tokens', models.BooleanField(default=False)),
                ('needs_value', models.PositiveSmallIntegerField()),
                ('produces', models.ForeignKey(related_name='value_conversions_producing', to='game.BoardTokenType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Turn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('number', models.PositiveIntegerField(default=1, db_index=True)),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('end', models.DateTimeField(null=True, blank=True)),
                ('match', models.ForeignKey(to='game.Match')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TurnStep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('step', models.PositiveSmallIntegerField(default=1, db_index=True)),
                ('report', models.TextField(default='')),
                ('turn', models.ForeignKey(related_name='steps', to='game.Turn')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='turnstep',
            unique_together=set([('turn', 'step')]),
        ),
        migrations.AlterUniqueTogether(
            name='turn',
            unique_together=set([('match', 'number')]),
        ),
        migrations.AddField(
            model_name='playerinturnstep',
            name='turn_step',
            field=models.ForeignKey(related_name='players', to='game.TurnStep'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='playerinturnstep',
            unique_together=set([('match_player', 'turn_step')]),
        ),
        migrations.AddField(
            model_name='notification',
            name='player',
            field=models.ForeignKey(to='game.Player'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='matchplayer',
            name='player',
            field=models.ForeignKey(related_name='match_players', to='game.Player'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='matchplayer',
            unique_together=set([('match', 'player')]),
        ),
        migrations.AddField(
            model_name='match',
            name='owner',
            field=models.ForeignKey(related_name='owner_of', to='game.Player'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='mapregionlink',
            unique_together=set([('source', 'destination')]),
        ),
        migrations.AlterUniqueTogether(
            name='mapregion',
            unique_together=set([('map', 'name'), ('map', 'short_name')]),
        ),
        migrations.AddField(
            model_name='mapcountry',
            name='headquarters',
            field=models.ForeignKey(to='game.MapRegion', related_name='countries_with_this_headquarter', unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mapcountry',
            name='map',
            field=models.ForeignKey(related_name='countries', to='game.Map'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mapcountry',
            name='reserve',
            field=models.ForeignKey(to='game.MapRegion', related_name='countries_with_this_reserve', unique=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='mapcountry',
            unique_together=set([('map', 'name')]),
        ),
        migrations.AddField(
            model_name='invite',
            name='invitor',
            field=models.ForeignKey(to='game.Player'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='conversion',
            field=models.ForeignKey(null=True, to='game.TokenConversion', related_name='+', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='location',
            field=models.ForeignKey(null=True, to='game.MapRegion', related_name='+', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='move_destination',
            field=models.ForeignKey(null=True, to='game.MapRegion', related_name='+', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='player_in_turn',
            field=models.ForeignKey(related_name='commands', to='game.PlayerInTurnStep'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='token_type',
            field=models.ForeignKey(null=True, to='game.BoardTokenType', related_name='+', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='value_conversion',
            field=models.ForeignKey(null=True, to='game.TokenConversion', related_name='+', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='command',
            unique_together=set([('player_in_turn', 'order')]),
        ),
        migrations.AddField(
            model_name='boardtoken',
            name='owner',
            field=models.ForeignKey(related_name='tokens', to='game.PlayerInTurnStep'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boardtoken',
            name='position',
            field=models.ForeignKey(to='game.MapRegion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boardtoken',
            name='type',
            field=models.ForeignKey(to='game.BoardTokenType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='battle',
            name='captured_tokens',
            field=models.ManyToManyField(related_name='captured_in', to='game.BoardToken'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='battle',
            name='location',
            field=models.ForeignKey(related_name='battles', to='game.MapRegion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='battle',
            name='turn_step',
            field=models.ForeignKey(related_name='battles', to='game.TurnStep'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='battle',
            name='winner',
            field=models.ForeignKey(null=True, to='game.PlayerInTurnStep', related_name='battles', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='battle',
            name='winning_tokens',
            field=models.ManyToManyField(related_name='winning_in', to='game.BoardToken'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='battle',
            unique_together=set([('turn_step', 'location')]),
        ),
    ]
