from math import cos, pi, sqrt


class GameTile:
    CO = cos(pi / 6)

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._x = self.x * self.CO

    def dist(self, other):
        return sqrt((self._x - other._x) ** 2 + (self.y - other.y) ** 2)

    def neighbours(self):
        return [
            self + GameTile(-1, 0.5),
            self + GameTile(0, 1),
            self + GameTile(1, 0.5),
            self + GameTile(-1, -0.5),
            self + GameTile(0, -1),
            self + GameTile(1, -0.5),
        ]

    def in_boundaries(self, radius):
        return self.dist(GameTile(0, 0)) < radius

    def __add__(self, other):
        """Tiles are vectors and can as well express steps, can be added etc."""
        return GameTile(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return GameTile(self.x - other.x, self.y - other.y)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __str__(self):
        return "<%s %s>" % (self.x, self.y)

    def __repr__(self):
        return "<%s %s>" % (self.x, self.y)

    def __hash__(self):
        return round(2 * self.x) + 100 * round(2 * self.y)

    def _dist_to_axis(self, d0, dx, dy, c):
        return abs(self._x * dy - self.y * dx + c) / (d0 or 1)

    def raycast(self, other, go_through=False, valid_steps=None):
        """Used for los checks mostly"""
        CO = cos(pi / 6)
        d0 = self.dist(other)
        current_tile = self
        dx, dy = other._x - self._x, other.y - self.y
        c = - dy * self._x + dx * self.y

        while True:
            forward_tiles = [n for n in current_tile.neighbours() if n._dist_to_axis(d0, dx, dy, c) < 0.5001
                             and n.dist(other) < current_tile.dist(other)]
            for tile in forward_tiles:
                yield tile
            for forward_tile in forward_tiles.copy():
                if valid_steps and forward_tile not in valid_steps:
                    forward_tiles.remove(forward_tile)
            if forward_tiles:
                current_tile = forward_tiles[-1]
            else:
                if self != other and current_tile == other and go_through:
                    for tile in current_tile.raycast(current_tile + current_tile - self, go_through):
                        yield tile
                break

    def display_location(self):
        return 340 + 32 * (8 + self.x), 92 + 32 * (7 + self.y)

    def dict_dump(self):
        return "%.1f %.1f" % (self.x, self.y)

    @staticmethod
    def from_string(string):
        x, y = string.split(' ')
        return GameTile(float(x), float(y))

    @staticmethod
    def get_tile_for_mouse(mouse_pos):
        x = int((mouse_pos[0] - 340) // 32 - 8)
        if x % 2 == 0:
            y = int((mouse_pos[1] - 92) // 32 - 7)
        else:
            y = int((mouse_pos[1] - 108) // 32 - 7) + 0.5
        return GameTile(x, y)

    @staticmethod
    def all_tiles(radius):
        for i in range(-int(radius + 2), int(radius + 2)):
            for j in range(-int(radius + 2), int(radius + 2)):
                tile = GameTile(i, j + (i % 2) / 2)
                if tile.in_boundaries(radius):
                    yield tile
