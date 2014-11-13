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
            name='BoardToken',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
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
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=3)),
                ('image_file_name', models.CharField(max_length=30)),
                ('movements',
                 models.PositiveSmallIntegerField(help_text='Number of tiles this token can cross in one move')),
                ('strength', models.PositiveSmallIntegerField()),
                ('purchasable', models.BooleanField(default=False,
                                                    help_text='Purchasable tokens can be bought with power pointsequivalent to their strength')),
                ('one_water_cross_per_movement', models.BooleanField(default=False)),
                ('can_be_on_land', models.BooleanField(default=False)),
                ('can_be_on_water', models.BooleanField(default=False)),
                ('can_capture_flag', models.BooleanField(default=False)),
                ('special_missile', models.BooleanField(default=False)),
                ('special_attack_reserves', models.BooleanField(default=False, help_text='Can attack reserves')),
                ('special_destroys_all', models.BooleanField(default=False, help_text='Infinite strength, beats all')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Command',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField()),
                ('type', models.CharField(
                    choices=[('MOV', 'Move'), ('TCO', 'Token conversion'), ('VCO', 'Value conversion'),
                             ('BUY', 'Token purchase')], max_length=3)),
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
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=75, unique=True)),
                ('valid', models.BooleanField(default=True)),
                ('code', models.CharField(db_index=True, max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Map',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('num_seats', models.IntegerField(help_text='Number of seats of this map')),
                ('name', models.CharField(max_length=30)),
                ('image_file_name', models.CharField(max_length=30)),
                ('public', models.BooleanField(default=False,
                                               help_text='Public maps can be used when players set up a new match')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapCountry',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
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
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=3)),
                ('land', models.BooleanField(default=False)),
                ('water', models.BooleanField(default=False)),
                ('render_on_map', models.BooleanField(default=True)),
                ('position_x', models.PositiveSmallIntegerField(default=0)),
                ('position_y', models.PositiveSmallIntegerField(default=0)),
                ('size_x', models.PositiveSmallIntegerField(default=0)),
                ('size_y', models.PositiveSmallIntegerField(default=0)),
                ('country', models.ForeignKey(blank=True, null=True, to='game.MapCountry')),
                ('map', models.ForeignKey(to='game.Map', related_name='regions')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapRegionLink',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('unidirectional', models.BooleanField(default=False)),
                ('crossing_water', models.BooleanField(default=False)),
                ('destination', models.ForeignKey(to='game.MapRegion', related_name='links_destination')),
                ('source', models.ForeignKey(to='game.MapRegion', related_name='links_source')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('status', models.CharField(
                    choices=[('SET', 'Set up'), ('SUA', 'Aborted (when in setup)'), ('PLA', 'Playing'),
                             ('PAU', 'Paused'), ('FIN', 'Finished'), ('ABO', 'Aborted (when in progress)')],
                    max_length=3)),
                ('public', models.BooleanField(default=False)),
                ('time_limit', models.DateTimeField(blank=True, null=True)),
                ('round_time_limit', models.DateTimeField(blank=True, null=True)),
                ('map', models.ForeignKey(to='game.Map', related_name='matches')),
            ],
            options={
                'verbose_name_plural': 'Matches',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MatchPlayer',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('setup_ready', models.BooleanField(default=False)),
                ('timeout_requested', models.BooleanField(default=False)),
                ('left_match', models.BooleanField(default=False)),
                ('defeated', models.BooleanField(default=False)),
                ('country', models.ForeignKey(blank=True, related_name='players', null=True, to='game.MapCountry')),
                ('match', models.ForeignKey(to='game.Match', related_name='players')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('read', models.BooleanField(default=False)),
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
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlayerInTurn',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('power_points', models.PositiveSmallIntegerField()),
                ('defeated', models.BooleanField(default=False)),
                ('total_strength', models.PositiveIntegerField(default=0)),
                ('timeout_requested', models.BooleanField(default=False)),
                ('ready', models.BooleanField(default=False)),
                ('left_match', models.BooleanField(default=False)),
                ('match_player', models.ForeignKey(to='game.MatchPlayer', related_name='+')),
            ],
            options={
                'verbose_name_plural': 'Players in turn',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TokenConversion',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('needs_quantity', models.PositiveSmallIntegerField(default=3)),
                ('produces_quantity', models.PositiveSmallIntegerField(default=1)),
                ('needs', models.ForeignKey(to='game.BoardTokenType', related_name='conversions_sourced')),
                ('produces', models.ForeignKey(to='game.BoardTokenType', related_name='conversions_producing')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TokenValueConversion',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('from_points', models.BooleanField(default=False)),
                ('from_tokens', models.BooleanField(default=False)),
                ('needs_value', models.PositiveSmallIntegerField()),
                ('produces', models.ForeignKey(to='game.BoardTokenType', related_name='value_conversions_producing')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Turn',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('number', models.PositiveIntegerField()),
                ('step', models.PositiveSmallIntegerField(default=0)),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('end', models.DateTimeField(blank=True, null=True)),
                ('report', models.TextField(default='')),
                ('match', models.ForeignKey(to='game.Match')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='playerinturn',
            name='turn',
            field=models.ForeignKey(to='game.Turn'),
            preserve_default=True,
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
            field=models.ForeignKey(to='game.Player', related_name='match_players'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='match',
            name='owner',
            field=models.ForeignKey(to='game.Player', related_name='owner_of'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mapcountry',
            name='headquarters',
            field=models.ForeignKey(related_name='countries_with_this_headquarter', to='game.MapRegion', unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mapcountry',
            name='map',
            field=models.ForeignKey(to='game.Map', related_name='countries'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mapcountry',
            name='reserve',
            field=models.ForeignKey(related_name='countries_with_this_reserve', to='game.MapRegion', unique=True),
            preserve_default=True,
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
            field=models.ForeignKey(blank=True, related_name='+', null=True, to='game.TokenConversion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='location',
            field=models.ForeignKey(blank=True, related_name='+', null=True, to='game.MapRegion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='move_destination',
            field=models.ForeignKey(blank=True, related_name='+', null=True, to='game.MapRegion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='player_in_turn',
            field=models.ForeignKey(to='game.PlayerInTurn', related_name='commands'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='token_type',
            field=models.ForeignKey(blank=True, related_name='+', null=True, to='game.BoardTokenType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='value_conversion',
            field=models.ForeignKey(blank=True, related_name='+', null=True, to='game.TokenConversion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boardtoken',
            name='owner',
            field=models.ForeignKey(to='game.PlayerInTurn', related_name='tokens'),
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
    ]
