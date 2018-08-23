from combat import *
from gametile import GameTile
from worldmap import *
from items import HealthPotion
import mock


class FakeCombat:
    def __init__(self):
        self.creatures = {}


class TestGametile:
    def setup(self):
        self.t1 = GameTile(2, 2)
        self.t2 = GameTile(3, 4.5)

    def test_tile_add(self):
        t = self.t1 + self.t2

        assert t.x == 5
        assert t.y == 6.5

    def test_tile_sub(self):
        t = self.t2 - self.t1

        assert t.x == 1
        assert t.y == 2.5

    def test_tile_dist(self):
        # +1 +0.5 is a hex move
        t1 = GameTile(5, 2.5)
        t2 = GameTile(3, 1.5)

        d = t1.dist(t2)

        assert round(d, ndigits=10) == 2

    def test_tile_compare(self):
        t1_bis = GameTile(2.0, 2)

        assert self.t1 == t1_bis
        assert self.t2 != t1_bis

    def test_mouse_location(self):
        xt1, yt1 = self.t1.display_location()

        assert GameTile.get_tile_for_mouse((xt1, yt1)) == self.t1
        assert GameTile.get_tile_for_mouse((xt1 + 20, yt1 + 20)) == self.t1

    def test_raycast(self):
        ray = list(self.t1.raycast(self.t2))

        assert GameTile(2, 3) in ray
        assert GameTile(3, 3.5) in ray
        assert GameTile(3, 4.5) in ray
        assert len(ray) == 3


class TestCreature:
    def test_init(self):
        c = Creature('Archer')
        assert c.health == 80
        assert c.maxhealth == 80
        assert c.damage == 12
        assert len(c.abilities) == 1
        assert c.abilities[0].name == 'Fire arrow'

    def test_takedamage(self):
        c = Creature('Archer')
        c.shield = 5

        c.take_damage(10, 'magic')

        assert c.health == 75

    def test_move(self):
        c = Creature('Barbarian')
        c.set_in_combat(FakeCombat(), GameTile(0, 0), 0)
        
        c.move_or_attack(GameTile(0, 1))

        assert c.tile == GameTile(0, 1)
        assert c.free_moves == 0
        assert c.next_action == 0

    def test_two_move(self):
        c = Creature('Barbarian')
        c.set_in_combat(FakeCombat(), GameTile(0, 0), 0)

        c.move_or_attack(GameTile(0, 1))
        c.move_or_attack(GameTile(0, 2))

        assert c.tile == GameTile(0, 2)
        assert c.free_moves == 1
        assert c.next_action == 100

    def test_attack(self):
        f = FakeCombat()
        c1 = Creature('Archer', is_pc=True)
        c2 = Creature('Archer', is_pc=False)
        c1.set_in_combat(f, GameTile(0, 0), 0)
        c2.set_in_combat(f, GameTile(0, 1), 0)
        
        c1.move_or_attack(GameTile(0, 1))

        assert c1.tile == GameTile(0, 0)
        assert c1.next_action == 100
        assert c2.health == c2.maxhealth - c1.damage

    def test_cleave(self):
        f = FakeCombat()
        c1 = Creature('Barbarian', is_pc=True)
        c2 = Creature('Archer', is_pc=False)
        c1.set_in_combat(f, GameTile(0, 0), 0)
        c2.set_in_combat(f, GameTile(0, 1), 0)

        c1.use_ability(c1.abilities[0], c1.tile)

        assert c1.next_action == 100
        assert c1.abilities[0].current_cooldown == 200
        assert c2.health == c2.maxhealth - c1.damage
        assert c1.health == c1.maxhealth

    def test_fireball(self):
        f = FakeCombat()
        c1 = Creature('Wizard', is_pc=True)
        c2 = Creature('Archer', is_pc=False)
        c3 = Creature('Archer', is_pc=False)
        c1.set_in_combat(f, GameTile(0, 0), 0)
        c2.set_in_combat(f, GameTile(0, 1), 0)
        c3.set_in_combat(f, GameTile(1, 0.5), 0)

        c1.use_ability(c1.abilities[0], c2.tile)

        assert c1.abilities[0].current_cooldown == 200
        assert c2.health == c2.maxhealth - 15
        assert c3.health == c3.maxhealth - 11
        assert c1.health == c1.maxhealth


class TestCombat:
    def test_targets(self):
        c1 = Creature('Archer', is_pc=True)
        g = Combat([(c1, (0, 0))], [('Skeleton', (0, 1))])

        targets = g.get_valid_targets(c1, c1.abilities[0])

        assert targets == [GameTile(0, 1)]

    def test_range(self):
        c1 = Creature('Archer', is_pc=True)
        g = Combat([(c1, (0, 0))], [('Skeleton', (0, 1))])

        hint = g.get_range_hint(c1, c1.abilities[0])

        assert GameTile(0, 2) not in hint
        assert GameTile(0, -2) in hint
        assert GameTile(1, -1.5) in hint


class TestWorldMap:
    @mock.patch('worldmap.TextSprite', mock.MagicMock())
    @mock.patch('worldmap.SimpleSprite', mock.MagicMock())
    def setup(self):
        self.wm = WorldInterface(None)

    def test_start(self):
        self.wm.new_game(4)

        assert self.wm.current_question_key == 'start'
        assert len(self.wm.pc_list) == 5

    @mock.patch('worldmap.TextSprite', mock.MagicMock())
    @mock.patch('worldmap.SimpleSprite', mock.MagicMock())
    @mock.patch('display.DISPLAY', mock.MagicMock())
    def test_potion(self):
        pot = HealthPotion('test', 'tiles/red-potion.png', 0)
        self.wm.new_game(4)
        self.wm.inventory.append(pot)
        self.wm.pc_list[0].health = 1
        ei = EquipInterface(self.wm, pot)

        ei.equip('1')

        assert self.wm.pc_list[0].health == self.wm.pc_list[0].maxhealth
        assert self.wm.inventory == []
