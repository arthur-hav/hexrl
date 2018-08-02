import display
import defs
from math import *
from pygame.locals import *

CREATURES = {}
DISPLAY = display.Display()

class GameTile():
    CO = cos(pi/6)
    MAP_RADIUS = 7.25
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._x = self.x * self.CO
    
    def dist(self, other):
        return sqrt((self._x-other._x)**2 + (self.y-other.y)**2)

    def neighbours(self):
        return [ self + GameTile(0, -1), 
            self + GameTile(1, -0.5), 
            self + GameTile(1, 0.5), 
            self + GameTile(0, 1), 
            self + GameTile(-1, 0.5), 
            self + GameTile(-1, -0.5) ]
    
    def in_boundaries(self):
        return self.dist(GameTile(0,0)) < self.MAP_RADIUS


    def __add__ (self, other):
        """Tiles are vectors and can as well express steps, can be added etc."""
        return GameTile(self.x + other.x, self.y + other.y)

    def __sub__ (self, other):
        return GameTile(self.x - other.x, self.y - other.y)

    def __eq__ (self, other):
        return self.dist(other) < 0.001

    def __str__ (self):
        return "<%s %s>" % (self.x, self.y)

    def __repr__ (self):
        return "<%s %s>" % (self.x, self.y)

    def __hash__ (self):
        return hash(( int(2 * self.x) , int(2 * self.y)))

    def _dist_to_axis(self, d0, dx, dy, c):
        return abs(self._x * dy - self.y * dx + c) / (d0 or 1)

    def ray_cast(self, other, go_through = False):
        """Used for los checks mostly"""
        CO = cos(pi/6)
        d0 = self.dist(other)
        current_tile = self
        dx, dy = other._x - self._x, other.y - self.y
        c = - dy * self._x + dx * self.y

        while True:
            forward_tiles = [n for n in current_tile.neighbours() if n._dist_to_axis(d0, dx, dy, c) < 0.5001
                    and n.dist(other) < current_tile.dist(other)
                    and n.in_boundaries() ]
            for tile in forward_tiles:
                yield tile
            if forward_tiles:
                current_tile = forward_tiles[-1]
            else:
                if self != other and current_tile == other and go_through:
                    for tile in current_tile.ray_cast(current_tile + current_tile - self):
                        yield tile
                break
        else:
            yield current_tile

class Entity (display.SimpleSprite):
    def __init__ (self, game_tile, image, is_pc = False, **kwargs):
        self.tile = game_tile
        self.is_pc = is_pc
        super(Entity, self).__init__('tiles/' + image + '.png', **kwargs)
        self.rect.x = 208 + 32 * (8 + self.tile.x)
        self.rect.y = 60 + 32 * (7 + self.tile.y)

    def step_to(self, target):
        return min(self.tile.neighbours(), key = lambda x: x.dist(target))


class Creature (Entity):
    def __init__ (self, game_tile, creaturedef):
        self.health = creaturedef['health']
        self.is_pc = creaturedef['is_pc']
        self.damage = creaturedef['damage']
        self.creaturedef = creaturedef
        self.portrait = 'portraits/' + creaturedef['portrait']
        self.next_action = 0
        super(Creature, self).__init__(game_tile, creaturedef['image'], creaturedef['is_pc'])

    def move_or_attack(self, destination):
        self.next_action += 4
        if destination in CREATURES or not destination.in_boundaries():
            return self.attack(destination)
        del CREATURES[self.tile]
        self.tile = destination
        self.rect.x = 208 + 32 * (8 + self.tile.x)
        self.rect.y = 60 + 32 * (7 + self.tile.y)
        CREATURES[destination] = self

    def attack(self, destination):
        CREATURES[destination].take_damage(self.damage)

    def take_damage(self, number):
        self.health -= number
        if self.health < 0:
            del CREATURES[self.tile]
            self.erase()

    def ai_play(self):
        nearest_pc = min( [c for c in CREATURES.values() if c.is_pc], 
                key= lambda x: x.tile.dist(self.tile))
        self.move_or_attack(self.step_to(nearest_pc.tile))

class HoverDisplay ():
    def __init__ (self):
        self.portrait = display.SimpleSprite('portraits/Empty.png')
        self.portrait.rect.x, self.portrait.rect.y = 20, 60
        self.ui_health = display.SimpleSprite('icons/heart.png')
        self.ui_health.rect.x, self.ui_health.rect.y = 20, 120
        self.gauge = display.Gauge(16, 0,'#FF0000')
        self.gauge.rect.x = 52
        self.gauge.rect.y = 128

    def update(self, creature):
        self.portrait.animate(creature.portrait)
        self.gauge.set_size(68  * creature.health // creature.creaturedef['health'] * 2)

class Game():
    def __init__(self):
        self.turn = 0
        self.spawn_creatures()
        #Will be set by new turn, only here declaring
        self.active_pc = None
        self.new_turn()
        self.hover_display = HoverDisplay()

    def active_pc(self):
        return self.pc_list[self.active]

    def spawn_creatures(self):
        CREATURES[GameTile(0, 6)] = Creature(GameTile(0, 6), defs.PC1)
        CREATURES[GameTile(0, 5)] = Creature(GameTile(0, 5), defs.PC2)
        CREATURES[GameTile(0, -6)] = Creature(GameTile(0,-6), defs.MOB1)

    def move_pc(self, tile):
        new_tile = self.active_pc.step_to(tile)
        CREATURES[self.active_pc.tile].move_or_attack(new_tile)
        self.new_turn()

    def new_turn(self):
        while True:
            to_act = min(CREATURES.values(), key= lambda x: x.next_action)
            if to_act.is_pc:
                self.active_pc = to_act
                return
            to_act.ai_play()

    def update(self, tile):
        cr = self.active_pc
        if tile in CREATURES:
            cr = CREATURES[tile]
        self.hover_display.update(cr)

class GameInterface ():
    def __init__ (self, game):
        self.background = display.SimpleSprite('bg.png', layer=1)
        self.game = game
        self.board = {}
        self._add_board()
        DISPLAY.subscribe_update(self.update)
        DISPLAY.subscribe_key(K_ESCAPE, self.on_key)
        DISPLAY.subscribe_click(self.on_click)

    def _add_board(self):
        center = GameTile(0,0) 
        for i in range(-10, 10):
            for j in range(-10, 10):
                tile = GameTile(i, j + (i % 2)/2)
                if tile.in_boundaries():
                    self.board[tile] = Entity(tile, 'Green1', layer=2)

    def get_tile_for_mouse(self, mouse_pos):
        for tile, sprite in self.board.items():
            if sprite.rect.collidepoint(mouse_pos):
                return tile

    def on_click(self, mouse_pos):
        t = self.get_tile_for_mouse(mouse_pos)
        if t:
            self.game.move_pc(t)

    def on_key(self, mouse_pos):
        exit(0)

#
    def update(self, mouse_pos):
        for sprite in self.board.values():
            sprite.animate('tiles/Green1.png')

        #Highlight active player
        if self.game.active_pc:
            self.board[self.game.active_pc.tile].animate('tiles/Green2.png')
        t = self.get_tile_for_mouse(mouse_pos)
        if t:
            self.game.update(t)
    
class MainMenu():
    def __init__(self):
        self.background = display.SimpleSprite('menu.png')
        DISPLAY.subscribe_key(K_RETURN, self.on_key)
    def on_key(self, key):
        game = Game()
        gi = GameInterface(game)
        DISPLAY.unsubscribe_key(K_RETURN, self.on_key)
        self.background.erase()

#this calls the 'main' function when this script is executed
if __name__ == '__main__':
    m = MainMenu()
    DISPLAY.main()
