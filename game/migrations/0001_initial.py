# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoardToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('moved_this_turn', models.BooleanField(default=False)),
                ('retreat_from_draw', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoardTokenType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=3)),
                ('movements',
                 models.PositiveSmallIntegerField(help_text='Number of tiles this token can cross in one move')),
                ('strength', models.PositiveSmallIntegerField()),
                ('purchasable', models.BooleanField(
                    help_text='Purchasable tokens can be bought with power pointsequivalent to their strength',
                    default=False)),
                ('one_water_cross_per_movement', models.BooleanField(default=False)),
                ('can_be_on_land', models.BooleanField(default=False)),
                ('can_be_on_water', models.BooleanField(default=False)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('order', models.PositiveSmallIntegerField()),
                ('type', models.CharField(
                    choices=[('MOV', 'Move'), ('TCO', 'Token conversion'), ('VCO', 'Value conversion'),
                             ('BUY', 'Token purchase')], max_length=3)),
                ('valid', models.NullBooleanField()),
                ('buy_type', models.ForeignKey(to='game.BoardTokenType', blank=True, null=True, related_name='+')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Map',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('num_seats', models.IntegerField(help_text='Number of seats of this map')),
                ('name', models.CharField(max_length=30)),
                ('image_file_name', models.CharField(max_length=30)),
                ('public', models.BooleanField(help_text='Public maps can be used when players set up a new match')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapCountry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=30)),
            ],
            options={
                'verbose_name_plural': 'Map countries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapRegion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=3)),
                ('land', models.BooleanField()),
                ('water', models.BooleanField()),
                ('render_on_map', models.BooleanField(default=True)),
                ('position_x', models.PositiveSmallIntegerField(default=0)),
                ('position_y', models.PositiveSmallIntegerField(default=0)),
                ('size_x', models.PositiveSmallIntegerField(default=0)),
                ('size_y', models.PositiveSmallIntegerField(default=0)),
                ('country', models.ForeignKey(to='game.MapCountry', blank=True, null=True)),
                ('map', models.ForeignKey(to='game.Map')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapRegionLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('status', models.CharField(
                    choices=[('SET', 'Set up'), ('SUA', 'Aborted (when in setup)'), ('PLA', 'Playing'),
                             ('PAU', 'Paused'), ('FIN', 'Finished'), ('ABO', 'Aborted (when in progress)')],
                    max_length=3)),
                ('public', models.BooleanField(default=False)),
                ('map', models.ForeignKey(related_name='matches', to='game.Map')),
                ('owner', models.ForeignKey(related_name='owner_of', to='account.Player')),
            ],
            options={
                'verbose_name_plural': 'Matches',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MatchPlayer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('setup_ready', models.BooleanField(default=False)),
                ('country', models.ForeignKey(to='game.MapCountry', blank=True, null=True, related_name='players')),
                ('match', models.ForeignKey(related_name='players', to='game.Match')),
                ('player', models.ForeignKey(related_name='match_players', to='account.Player')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlayerInTurn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('power_points', models.PositiveSmallIntegerField()),
                ('total_strength', models.PositiveIntegerField(default=0)),
                ('timeout_requested', models.BooleanField(default=False)),
                ('ready', models.BooleanField(default=False)),
                ('flag_controlled_by',
                 models.ForeignKey(to='game.MatchPlayer', blank=True, null=True, related_name='+')),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('number', models.PositiveIntegerField()),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('end', models.DateTimeField(blank=True, null=True)),
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
            model_name='mapcountry',
            name='headquarters',
            field=models.ForeignKey(related_name='countries_with_this_headquarter', to='game.MapRegion'),
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
            field=models.ForeignKey(related_name='countries_with_this_reserve', to='game.MapRegion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='conversion',
            field=models.ForeignKey(to='game.TokenConversion', blank=True, null=True, related_name='+'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='location',
            field=models.ForeignKey(to='game.MapRegion', blank=True, null=True, related_name='+'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='move_destination',
            field=models.ForeignKey(to='game.MapRegion', blank=True, null=True, related_name='+'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='player_in_turn',
            field=models.ForeignKey(to='game.PlayerInTurn'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='command',
            name='value_conversion',
            field=models.ForeignKey(to='game.TokenConversion', blank=True, null=True, related_name='+'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boardtoken',
            name='owner',
            field=models.ForeignKey(related_name='tokens', to='game.PlayerInTurn'),
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
