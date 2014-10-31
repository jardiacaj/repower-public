from django.db import migrations

from game.models import Map, MapCountry, MapRegion, MapRegionLink, BoardTokenType, TokenConversion, TokenValueConversion


def insert_token_types(apps, schema_editor):
    infantry = BoardTokenType(name="Infantry", short_name="IN", movements=2, strength=2, purchasable=True,
                              one_water_cross_per_movement=True, can_be_on_land=True, image_file_name="infantry")
    infantry.save()
    small_tank = BoardTokenType(name="Small Tank", short_name="S-T", movements=3, strength=3, purchasable=True,
                                one_water_cross_per_movement=True, can_be_on_land=True, image_file_name="small-tank")
    small_tank.save()
    fighter = BoardTokenType(name="Fighter", short_name="F", movements=5, strength=5, purchasable=True,
                             one_water_cross_per_movement=False, can_be_on_land=True, image_file_name="fighter")
    fighter.save()
    destroyer = BoardTokenType(name="Destroyer", short_name="D", movements=1, strength=10, purchasable=True,
                               one_water_cross_per_movement=False, can_be_on_water=True, image_file_name="destroyer")
    destroyer.save()

    regiment = BoardTokenType(name="Regiment", short_name="REG", movements=2, strength=20, purchasable=False,
                              one_water_cross_per_movement=True, can_be_on_land=True, image_file_name="regiment")
    regiment.save()
    tank = BoardTokenType(name="Tank", short_name="TNK", movements=3, strength=30, purchasable=False,
                          one_water_cross_per_movement=True, can_be_on_land=True, image_file_name="tank")
    tank.save()
    bomber = BoardTokenType(name="Bomber", short_name="B", movements=5, strength=25, purchasable=False,
                            one_water_cross_per_movement=False, can_be_on_land=True, image_file_name="bomber")
    bomber.save()
    cruiser = BoardTokenType(name="Cruiser", short_name="C", movements=1, strength=50, purchasable=False,
                             one_water_cross_per_movement=False, can_be_on_water=True, image_file_name="cruiser")
    cruiser.save()

    mega_missile = BoardTokenType(name="Mega-Missile", short_name="M-M", movements=0, strength=0, purchasable=False,
                                  image_file_name="mega-missile",
                                  can_be_on_land=True,
                                  special_destroys_all=True,
                                  one_water_cross_per_movement=False,
                                  special_attack_reserves=True,
                                  special_missile=True)
    mega_missile.save()

    TokenConversion(needs=infantry, produces=regiment).save()
    TokenConversion(needs=small_tank, produces=tank).save()
    TokenConversion(needs=fighter, produces=bomber).save()
    TokenConversion(needs=destroyer, produces=cruiser).save()

    TokenValueConversion(from_tokens=True, needs_value=100, produces=mega_missile)


def insert_maps(apps, schema_editor):
    two_player_map = Map(num_seats=2, name="Alpha", image_file_name="alpha", public=True)
    two_player_map.save()

    south_hq = MapRegion(map=two_player_map, name='South HQ', short_name='SHQ', position_x=260, position_y=575,
                         size_x=130, size_y=75, land=True, water=True)
    south_hq.save()
    north_hq = MapRegion(map=two_player_map, name='North HQ', short_name='NHQ', position_x=260, position_y=000,
                         size_x=130, size_y=75, land=True, water=True)
    north_hq.save()
    south_reserve = MapRegion(map=two_player_map, name='South Reserve', short_name='SRe', render_on_map=False,
                              land=True, water=True)
    south_reserve.save()
    north_reserve = MapRegion(map=two_player_map, name='North Reserve', short_name='NRe', render_on_map=False,
                              land=True, water=True)
    north_reserve.save()

    north_country = MapCountry(map=two_player_map, name="North", headquarters=north_hq, reserve=north_reserve,
                               color_rgb="00DD00", color_gif_palette=118)
    north_country.save()
    south_country = MapCountry(map=two_player_map, name="South", headquarters=south_hq, reserve=south_reserve,
                               color_rgb="FF851C", color_gif_palette=89)
    south_country.save()

    south_hq.country = south_country
    south_hq.save()
    south_reserve.country = south_country
    south_reserve.save()
    north_hq.country = north_country
    north_hq.save()
    north_reserve.country = north_country
    north_reserve.save()

    ocean = dict()
    ocean[1] = MapRegion(position_x=520, position_y=150, size_x=130, size_y=75)
    ocean[2] = MapRegion(position_x=520, position_y=000, size_x=130, size_y=75)
    ocean[3] = MapRegion(position_x=000, position_y=000, size_x=130, size_y=75)
    ocean[4] = MapRegion(position_x=000, position_y=150, size_x=130, size_y=75)
    ocean[5] = MapRegion(position_x=000, position_y=350, size_x=130, size_y=75)
    ocean[6] = MapRegion(position_x=000, position_y=575, size_x=130, size_y=75)
    ocean[7] = MapRegion(position_x=520, position_y=575, size_x=130, size_y=75)
    ocean[8] = MapRegion(position_x=520, position_y=350, size_x=130, size_y=75)
    ocean[9] = MapRegion(position_x=130, position_y=300, size_x=390, size_y=50)

    for key, region in ocean.items():
        region.land = False
        region.water = True
        region.map = two_player_map
        region.name = "Ocean %d" % key
        region.short_name = "Oc%d" % key
        region.save()

    north = dict()
    north[1] = MapRegion(position_x=390, position_y=75, water=True, size_x=130, size_y=75)
    north[2] = MapRegion(position_x=260, position_y=75, water=True, size_x=130, size_y=75)
    north[3] = MapRegion(position_x=130, position_y=75, water=True, size_x=130, size_y=75)
    north[4] = MapRegion(position_x=390, position_y=150, water=True, size_x=130, size_y=75)
    north[5] = MapRegion(position_x=260, position_y=150, water=False, size_x=130, size_y=75)
    north[6] = MapRegion(position_x=130, position_y=150, water=True, size_x=130, size_y=75)
    north[7] = MapRegion(position_x=390, position_y=225, water=True, size_x=130, size_y=75)
    north[8] = MapRegion(position_x=260, position_y=225, water=True, size_x=130, size_y=75)
    north[9] = MapRegion(position_x=130, position_y=225, water=True, size_x=130, size_y=75)

    for key, region in north.items():
        region.land = True
        region.map = two_player_map
        region.country = north_country
        region.name = "North %d" % key
        region.short_name = "No%d" % key
        region.save()

    south = dict()
    south[1] = MapRegion(position_x=130, position_y=500, water=True, size_x=130, size_y=75)
    south[2] = MapRegion(position_x=260, position_y=500, water=True, size_x=130, size_y=75)
    south[3] = MapRegion(position_x=390, position_y=500, water=True, size_x=130, size_y=75)
    south[4] = MapRegion(position_x=130, position_y=425, water=True, size_x=130, size_y=75)
    south[5] = MapRegion(position_x=260, position_y=425, water=False, size_x=130, size_y=75)
    south[6] = MapRegion(position_x=390, position_y=425, water=True, size_x=130, size_y=75)
    south[7] = MapRegion(position_x=130, position_y=350, water=True, size_x=130, size_y=75)
    south[8] = MapRegion(position_x=260, position_y=350, water=True, size_x=130, size_y=75)
    south[9] = MapRegion(position_x=390, position_y=350, water=True, size_x=130, size_y=75)

    for key, region in south.items():
        region.land = True
        region.map = two_player_map
        region.country = south_country
        region.name = "South %d" % key
        region.short_name = "So%d" % key
        region.save()

    west_island = MapRegion(map=two_player_map, name="West Island", short_name="WIs", position_x=000, position_y=300,
                            land=True, water=True, size_x=130, size_y=50)
    west_island.save()
    east_island = MapRegion(map=two_player_map, name="East Island", short_name="EIs", position_x=520, position_y=300,
                            land=True, water=True, size_x=130, size_y=50)
    east_island.save()

    MapRegionLink(source=north_reserve, destination=north_hq, unidirectional=True).save()
    MapRegionLink(source=south_reserve, destination=south_hq, unidirectional=True).save()

    MapRegionLink(source=north_hq, destination=ocean[2]).save()
    MapRegionLink(source=north_hq, destination=ocean[3]).save()
    MapRegionLink(source=north_hq, destination=north[1], crossing_water=True).save()
    MapRegionLink(source=north_hq, destination=north[2], crossing_water=True).save()
    MapRegionLink(source=north_hq, destination=north[3], crossing_water=True).save()

    MapRegionLink(source=south_hq, destination=ocean[6]).save()
    MapRegionLink(source=south_hq, destination=ocean[7]).save()
    MapRegionLink(source=south_hq, destination=south[1], crossing_water=True).save()
    MapRegionLink(source=south_hq, destination=south[2], crossing_water=True).save()
    MapRegionLink(source=south_hq, destination=south[3], crossing_water=True).save()

    MapRegionLink(source=west_island, destination=ocean[4]).save()
    MapRegionLink(source=west_island, destination=ocean[5]).save()
    MapRegionLink(source=west_island, destination=ocean[9]).save()
    MapRegionLink(source=west_island, destination=north[9], crossing_water=True).save()
    MapRegionLink(source=west_island, destination=south[7], crossing_water=True).save()

    MapRegionLink(source=east_island, destination=ocean[1]).save()
    MapRegionLink(source=east_island, destination=ocean[8]).save()
    MapRegionLink(source=east_island, destination=ocean[9]).save()
    MapRegionLink(source=east_island, destination=north[7], crossing_water=True).save()
    MapRegionLink(source=east_island, destination=south[9], crossing_water=True).save()

    MapRegionLink(source=ocean[1], destination=ocean[2]).save()
    MapRegionLink(source=ocean[1], destination=north[1]).save()
    MapRegionLink(source=ocean[1], destination=north[4]).save()
    MapRegionLink(source=ocean[1], destination=north[7]).save()
    MapRegionLink(source=ocean[1], destination=ocean[9]).save()

    MapRegionLink(source=ocean[2], destination=north[5]).save()
    MapRegionLink(source=ocean[2], destination=north[2]).save()
    MapRegionLink(source=ocean[2], destination=north[1]).save()
    MapRegionLink(source=ocean[2], destination=north[4]).save()

    MapRegionLink(source=ocean[3], destination=north[2]).save()
    MapRegionLink(source=ocean[3], destination=north[6]).save()
    MapRegionLink(source=ocean[3], destination=ocean[4]).save()

    MapRegionLink(source=ocean[4], destination=north[3]).save()
    MapRegionLink(source=ocean[4], destination=north[6]).save()
    MapRegionLink(source=ocean[4], destination=north[9]).save()

    MapRegionLink(source=ocean[5], destination=ocean[9]).save()
    MapRegionLink(source=ocean[5], destination=ocean[6]).save()
    MapRegionLink(source=ocean[5], destination=south[7]).save()
    MapRegionLink(source=ocean[5], destination=south[1]).save()
    MapRegionLink(source=ocean[5], destination=south[2]).save()
    MapRegionLink(source=ocean[5], destination=south[4]).save()

    MapRegionLink(source=ocean[6], destination=south[1]).save()
    MapRegionLink(source=ocean[6], destination=south[2]).save()
    MapRegionLink(source=ocean[6], destination=south[4]).save()

    MapRegionLink(source=ocean[7], destination=ocean[8]).save()
    MapRegionLink(source=ocean[7], destination=south[2]).save()
    MapRegionLink(source=ocean[7], destination=south[3]).save()
    MapRegionLink(source=ocean[7], destination=south[6]).save()

    MapRegionLink(source=ocean[8], destination=ocean[9]).save()
    MapRegionLink(source=ocean[8], destination=south[9]).save()
    MapRegionLink(source=ocean[8], destination=south[6]).save()
    MapRegionLink(source=ocean[8], destination=south[3]).save()

    MapRegionLink(source=ocean[9], destination=north[7]).save()
    MapRegionLink(source=ocean[9], destination=north[8]).save()
    MapRegionLink(source=ocean[9], destination=north[9]).save()
    MapRegionLink(source=ocean[9], destination=south[7]).save()
    MapRegionLink(source=ocean[9], destination=south[8]).save()
    MapRegionLink(source=ocean[9], destination=south[9]).save()

    three_by_three_links = {
        1: [2, 4, 5],
        2: [3, 4, 5, 6],
        3: [5, 6],
        4: [5, 7, 8],
        5: [6, 7, 8, 9],
        6: [8, 9],
        7: [8, ],
        8: [9, ],
    }

    for source, destinations in three_by_three_links.items():
        for destination in destinations:
            MapRegionLink(source=north[source], destination=north[destination]).save()
            MapRegionLink(source=south[source], destination=south[destination]).save()

    Map(num_seats=4, name="Proto-4", image_file_name="proto4", public=True).save()


# NUM PXX PXY NOMBRE---- ACHT LNKT
# M2alpha             02031
# 000 260 575 SUR-HQ     0111 026- 027* 028* 029* 030-
# 001 000 000 OCEANO3    1000 002- 004- 005- 007- 008-
# 002 260 000 NORTE-HQ   0122 001- 003- 004* 005* 006*
# 003 390 000 OCEANO2    1000 002- 005- 006- 010- 011-
# 004 130 075 NORTE3     0102 001- 002* 005- 007- 008- 009-
# 005 260 075 NORTE2     0102 001- 002* 003- 004- 006- 008- 009- 010-
# 006 390 075 NORTE1     0102 002* 003- 005- 009- 010- 011-
# 007 000 150 OCEANO4    1000 001- 004- 008- 012- 015- 016-
# 008 130 150 NORTE6     0102 001- 004- 005- 007- 009- 012- 013-
# 009 260 150 NORTE5     0002 004- 005- 006- 008- 010- 012- 013- 014-
# 010 390 150 NORTE4     0102 003- 005- 006- 009- 011- 013- 014-
# 011 520 150 OCEANO1    1000 003- 006- 010- 014- 016- 017-
# 012 130 225 NORTE9     0102 007- 008- 009- 013- 015* 016-
# 013 260 225 NORTE8     0102 008- 009- 010- 012- 014- 016-
# 014 390 225 NORTE7     0102 009- 010- 011- 013- 016- 017*
# 015 000 300 ISLA-OESTE 0100 007- 012* 016- 018- 019*
# 016 130 300 MARCENTRAL 1000 007- 011- 012- 013- 014- 015- 017- 018- 019- 020- 021- 022-
# 017 520 300 ISLA-ESTE  0100 011- 014* 016- 021* 022-
# 018 000 350 OCEANO5    1000 015- 016- 019- 023- 026- 027-
# 019 130 350 SUR7       0101 015* 016- 018- 020- 023- 024-
# 020 260 350 SUR8       0101 016- 019- 021- 023- 024- 025-
# 021 390 350 SUR9       0101 016- 017* 020- 022- 024- 025-
# 022 520 350 OCEANO8    1000 016- 017- 021- 025- 029- 030-
# 023 130 425 SUR4       0101 018- 019- 020- 024- 026- 027- 028-
# 024 260 425 SUR5       0001 019- 020- 021- 023- 025- 027- 028- 029-
# 025 390 425 SUR6       0101 020- 021- 022- 024- 028- 029- 030-
# 026 000 500 OCEANO6    1000 018- 023- 027- 028- 000-
# 027 130 500 SUR1       0101 018- 023- 024- 026- 028- 000*
# 028 260 500 SUR2       0101 023- 024- 025- 026- 027- 029- 030- 000*
# 029 390 500 SUR3       0101 022- 024- 025- 028- 030- 000*
# 030 390 575 OCEANO7    1000 022- 025- 028- 029- 000


class Migration(migrations.Migration):
    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insert_maps),
        migrations.RunPython(insert_token_types)
    ]