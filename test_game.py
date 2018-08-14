from game import *


class TestGametile():
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
