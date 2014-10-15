# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('account', '0001_initial'),
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoardToken',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoardTokenType',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=3)),
                ('movements', models.PositiveSmallIntegerField()),
                ('strength', models.PositiveSmallIntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Map',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('num_seats', models.IntegerField()),
                ('name', models.CharField(max_length=30)),
                ('image_file_name', models.CharField(max_length=30)),
                ('public', models.BooleanField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapCountry',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapRegion',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=3)),
                ('land', models.BooleanField()),
                ('water', models.BooleanField()),
                ('render_on_map', models.BooleanField(default=True)),
                ('position_x', models.PositiveSmallIntegerField(default=0)),
                ('position_y', models.PositiveSmallIntegerField(default=0)),
                ('size_x', models.PositiveSmallIntegerField(default=0)),
                ('size_y', models.PositiveSmallIntegerField(default=0)),
                ('country', models.ForeignKey(null=True, blank=True, to='game.MapCountry')),
                ('map', models.ForeignKey(to='game.Map')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MapRegionLink',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
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
            name='Movement',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('type', models.CharField(choices=[('MOV', 'Move'), ('CON', 'Conversion'), ('MMI', 'Mega-missile')],
                                          max_length=3)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlayerInTurn',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('power_points', models.PositiveSmallIntegerField()),
                ('flag_controlled_by', models.ForeignKey(to='game.PlayerInTurn')),
                ('match_player', models.ForeignKey(to='game.MatchPlayer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Turn',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('number', models.PositiveIntegerField()),
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
            model_name='movement',
            name='player_in_turn',
            field=models.ForeignKey(to='game.PlayerInTurn'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mapcountry',
            name='headquarters',
            field=models.ForeignKey(related_name='headquarters_players', to='game.MapRegion'),
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
            field=models.ForeignKey(related_name='reserve_players', to='game.MapRegion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boardtoken',
            name='owner',
            field=models.ForeignKey(to='game.PlayerInTurn'),
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
            model_name='match',
            name='map',
            field=models.ForeignKey(related_name='matches', default=None, to='game.Map'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='match',
            name='name',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='match',
            name='owner',
            field=models.ForeignKey(related_name='owner_of', default=None, to='account.Player'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='match',
            name='public',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='match',
            name='status',
            field=models.CharField(default='',
                                   choices=[('SET', 'Set up'), ('SUA', 'Aborted (when in setup)'), ('PLA', 'Playing'),
                                            ('PAU', 'Paused'), ('FIN', 'Finished'),
                                            ('ABO', 'Aborted (when in progress)')], max_length=3),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='matchplayer',
            name='country',
            field=models.ForeignKey(null=True, related_name='players', blank=True, to='game.MapCountry'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='matchplayer',
            name='player',
            field=models.ForeignKey(related_name='match_players', default=None, to='account.Player'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='matchplayer',
            name='ready',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='matchplayer',
            name='match',
            field=models.ForeignKey(related_name='players', to='game.Match'),
        ),
    ]
