import display
import defs
from math import *
from pygame.locals import *
import random

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
    def __init__ (self, game, game_tile, creaturedef):
        self.game = game
        self.health = creaturedef['health']
        self.is_pc = creaturedef['is_pc']
        self.damage = creaturedef['damage']
        self.creaturedef = creaturedef
        self.portrait = 'portraits/' + creaturedef['portrait']
        self.next_action = 0
        super(Creature, self).__init__(game_tile, creaturedef['image'], creaturedef['is_pc'])

    def move_or_attack(self, destination):
        self.next_action += 4
        if destination in self.game.creatures or not destination.in_boundaries():
            return self.attack(destination)
        del self.game.creatures[self.tile]
        self.tile = destination
        self.rect.x = 208 + 32 * (8 + self.tile.x)
        self.rect.y = 60 + 32 * (7 + self.tile.y)
        self.game.creatures[destination] = self

    def attack(self, destination):
        self.game.creatures[destination].take_damage(self.damage)

    def take_damage(self, number):
        self.health -= number
        if self.health < 0:
            del self.game.creatures[self.tile]
            self.erase()

    def ai_play(self):
        nearest_pc = min( [c for c in self.game.creatures.values() if c.is_pc], 
                key= lambda x: x.tile.dist(self.tile))
        self.move_or_attack(self.step_to(nearest_pc.tile))

class HoverDisplay ():
    def __init__ (self):
        self.portrait = display.SimpleSprite('portraits/P1.png')
        self.portrait.rect.x, self.portrait.rect.y = 20, 60
        self.ui_health = display.SimpleSprite('icons/heart.png')
        self.ui_health.rect.x, self.ui_health.rect.y = 20, 120
        self.gauge = display.Gauge(16, 0,'#FF0000')
        self.gauge.rect.x = 52
        self.gauge.rect.y = 128

    def update(self, creature):
        self.portrait.animate(creature.portrait)
        self.gauge.set_size(68  * creature.health // creature.creaturedef['health'] * 2)

    def erase_all(self):
        self.portrait.erase()
        self.ui_health.erase()
        self.gauge.erase()

class Game():
    def __init__(self):
        self.turn = 0
        self.creatures = {}
        self.spawn_creatures()
        #Will be set by new turn, only here declaring
        self.active_pc = None
        self.new_turn()
        self.hover_display = HoverDisplay()

    def active_pc(self):
        return self.pc_list[self.active]

    def spawn_creatures(self):
        self.creatures[GameTile(0, 6)] = Creature(self, GameTile(0, 6), defs.PC1)
        self.creatures[GameTile(0, 5)] = Creature(self, GameTile(0, 5), defs.PC2)
        self.creatures[GameTile(0, -6)] = Creature(self, GameTile(0,-6), defs.MOB1)

    def move_pc(self, tile):
        new_tile = self.active_pc.step_to(tile)
        self.creatures[self.active_pc.tile].move_or_attack(new_tile)
        self.new_turn()

    def new_turn(self):
        while True:
            to_act = min(self.creatures.values(), key= lambda x: x.next_action)
            if to_act.is_pc:
                self.active_pc = to_act
                return
            to_act.ai_play()

    def update(self, tile):
        cr = self.active_pc
        if tile in self.creatures:
            cr = self.creatures[tile]
        self.hover_display.update(cr)

    def is_over(self):
        return all((c.is_pc for c in self.creatures.values())) or all((not c.is_pc for c in self.creatures.values()))

    def erase_all(self):
        for c in self.creatures.values():
            c.erase()
        self.hover_display.erase_all()

class Interface ():
    def __init__(self, father, ui_sprite_name, keys=[]):
        self.father = father
        self.keys = keys
        self.ui_sprite_name = ui_sprite_name
        self.ui_sprite = display.SimpleSprite(ui_sprite_name, layer=1)
        if self.father:
            self.father.desactivate()
        self.activate()

    def desactivate(self):
        DISPLAY.unsubscribe_click(self.on_click)
        DISPLAY.unsubscribe_update(self.update)
        for k, v in self.keys:
            DISPLAY.unsubscribe_key(k, v)
        self.ui_sprite.erase()


    def activate(self):
        DISPLAY.subscribe_click(self.on_click)
        DISPLAY.subscribe_update(self.update)
        for k, v in self.keys:
            DISPLAY.subscribe_key(k, v)
        self.ui_sprite = display.SimpleSprite(self.ui_sprite_name, layer=1)

    def update(self, pos):
        pass

    def on_click(self, pos):
        pass

    def done(self):
        if self.father:
            self.father.activate()
        else:
            exit(0)

class GameInterface (Interface):
    def __init__ (self, father):
        self.game = Game()
        self.board = {}
        self._add_board()
        super(GameInterface, self).__init__(father, 'bg.png')

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
        if self.game.is_over():
            for tile in self.board.values():
                tile.erase()
            self.game.erase_all()
            self.done()
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
    
class MainMenuInterface(Interface):
    def __init__(self):
        super(MainMenuInterface, self).__init__(None, 'menu.png', keys = [
            (K_ESCAPE, self.done),
            (K_RETURN, self.start),
            ])
    def start(self, key):
        WorldInterface(self)

class WorldInterface(Interface):
    def __init__(self, father):
        self.world_map = {}
        self.pc_tile = GameTile(0, 0)
        super(WorldInterface, self).__init__(father, 'worldmap.png', keys = [
            (K_KP4, self.go_sw),
            (K_KP5, self.go_s),
            (K_KP6, self.go_se),
            (K_KP7, self.go_nw),
            (K_KP8, self.go_n),
            (K_KP9, self.go_ne)
            ])

    def go_s(self, _):
        self.go(self.pc_tile.neighbours()[0])

    def go_se(self, _):
        self.go(self.pc_tile.neighbours()[1])

    def go_ne(self, _):
        self.go(self.pc_tile.neighbours()[2])

    def go_n(self, _):
        self.go(self.pc_tile.neighbours()[3])

    def go_nw(self, _):
        self.go(self.pc_tile.neighbours()[4])

    def go_sw(self, _):
        self.go(self.pc_tile.neighbours()[5])

    def go(self, tile):
        self.start_game()

    def start_game(self):
        gi = GameInterface(self)

#this calls the 'main' function when this script is executed
if __name__ == '__main__':
    m = MainMenuInterface()
    DISPLAY.main()
