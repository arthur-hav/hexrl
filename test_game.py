import mock
from game import *


class FakeGame:
    def __init__(self):
        self.creatures = {}
        self.dmg_log_display = mock.Mock()


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
        c = Creature('Archer')
        c.set_in_game(FakeGame(), GameTile(0, 0), 0)
        
        c.move_or_attack(GameTile(0, 1))

        assert c.tile == GameTile(0, 1)
        assert c.next_action == 100

    def test_attack(self):
        f = FakeGame()
        c1 = Creature('Archer', is_pc=True)
        c2 = Creature('Archer', is_pc=False)
        c1.set_in_game(f, GameTile(0, 0), 0)
        c2.set_in_game(f, GameTile(0, 1), 0)
        
        c1.move_or_attack(GameTile(0, 1))

        assert c1.tile == GameTile(0, 0)
        assert c1.next_action == 100
        assert c2.health == c2.maxhealth - c1.damage

    def test_ability(self):
        f = FakeGame()
        c1 = Creature('Barbarian', is_pc=True)
        c2 = Creature('Archer', is_pc=False)
        c1.set_in_game(f, GameTile(0, 0), 0)
        c2.set_in_game(f, GameTile(0, 1), 0)
        
        c1.use_ability(c1.abilities[0], c1.tile)

        assert c1.next_action == 100
        assert c1.ability_cooldown[0] == 200
        assert c2.health == c2.maxhealth - round(1.2 * c1.damage)

