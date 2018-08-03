from display import Interface, TextSprite, SimpleSprite, Gauge
import defs
from math import *
from pygame.locals import *
import random

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

class Entity (SimpleSprite):
    def __init__ (self, game_tile, image, is_pc = False, **kwargs):
        self.tile = game_tile
        self.is_pc = is_pc
        self.image_name = 'tiles/' + image + '.png'
        super(Entity, self).__init__(self.image_name, **kwargs)
        self.rect.x = 208 + 32 * (8 + self.tile.x)
        self.rect.y = 92 + 32 * (7 + self.tile.y)

    def step_to(self, target):
        return min(self.tile.neighbours(), key = lambda x: x.dist(target))

class Creature():
    def __init__ (self, creaturedef):
        self.health = creaturedef['health']
        self.is_pc = creaturedef['is_pc']
        self.damage = creaturedef['damage']
        self.speed = creaturedef['speed']
        self.name = creaturedef['name']
        self.portrait = 'portraits/' + creaturedef['portrait']
        self.creaturedef = creaturedef
        self.entity = None
        self.game = None
        self.frames = []

    def set_in_game(self, game, game_tile, next_action):
        self.entity = Entity(game_tile, self.creaturedef['image'], self.creaturedef['is_pc'])
        self.game = game
        self.game.creatures[game_tile] = self
        self.next_action = next_action

    ### Below this : only valid if previously set_in_game

    def erase(self):
        self.entity.erase()
        self.game = None
        self.entity = None

    def update(self):
        if self.frames:
            self.entity.animate(self.frames.pop(0))

    def move_or_attack(self, destination):
        self.next_action += 1000 / self.speed
        if destination in self.game.creatures or not destination.in_boundaries():
            return self.attack(destination)
        del self.game.creatures[self.entity.tile]
        self.entity.tile = destination
        self.entity.rect.x = 208 + 32 * (8 + self.entity.tile.x)
        self.entity.rect.y = 92 + 32 * (7 + self.entity.tile.y)
        self.game.creatures[destination] = self

    def attack(self, destination):
        creature = self.game.creatures[destination]
        creature.take_damage(self.damage)
        self.game.log_display.push_text("%s hits %s for %d damage." % (self.name, creature.name, self.damage))

    def take_damage(self, number):
        self.health -= number
        self.frames.extend(['tiles/Hit.png', self.entity.image_name])
        if self.health < 0:
            self.game.log_display.push_text("%s dies." % (self.name))
            del self.game.creatures[self.entity.tile]
            self.erase()

    def ai_play(self):
        nearest_pc = min( [c for c in self.game.creatures.values() if c.is_pc], 
                key= lambda x: x.entity.tile.dist(self.entity.tile))
        self.move_or_attack(self.entity.step_to(nearest_pc.entity.tile))

class HoverDisplay ():
    def __init__ (self):
        self.portrait = SimpleSprite('portraits/P1.png')
        self.portrait.rect.x, self.portrait.rect.y = 20, 92
        self.ui_health = SimpleSprite('icons/heart.png')
        self.ui_health.rect.x, self.ui_health.rect.y = 20, 154
        self.gauge = Gauge(16, 0,'#FF0000')
        self.gauge.rect.x = 52
        self.gauge.rect.y = 160
        self.ui_damage = SimpleSprite('icons/sword.png')
        self.ui_damage.rect.x, self.ui_damage.rect.y = 20, 184
        self.ui_damage_stat = TextSprite('', '#ffffff', 60, 192)

    def update(self, creature):
        self.portrait.animate(creature.portrait)
        self.gauge.set_size(68  * creature.health // creature.creaturedef['health'] * 2)
        self.ui_damage_stat.set_text(str(creature.damage))

    def erase_all(self):
        self.portrait.erase()
        self.ui_health.erase()
        self.ui_damage.erase()
        self.ui_damage_stat.erase()
        self.gauge.erase()

class LogDisplay ():
    def __init__ (self):
        self.lines = []
        self.line_sprites = []

    def push_text(self, text):
        if len(self.line_sprites) >= 4:
            for sprite in self.line_sprites:
                sprite.rect.y -= 16
            self.line_sprites[0].erase()
            self.line_sprites.pop(0)
        sprite = TextSprite(text, '#ffffff', 208, 16 + len(self.line_sprites) * 16)
        self.line_sprites.append(sprite)
        self.lines.append(text)

    def erase_all(self):
        for line in self.line_sprites:
            line.erase()

class Game():
    def __init__(self, pc_list, mob_list):
        self.turn = 0
        self.creatures = {}
        self.board = {}
        self._add_board()
        self.spawn_creatures(pc_list, mob_list)
        #Will be set by new turn, only here declaring
        self.active_pc = None
        self.new_turn()
        self.hover_display = HoverDisplay()
        self.log_display = LogDisplay()

    def _add_board(self):
        center = GameTile(0,0) 
        for i in range(-10, 10):
            for j in range(-10, 10):
                tile = GameTile(i, j + (i % 2)/2)
                if tile.in_boundaries():
                    self.board[tile] = Entity(tile, 'Green1', layer=2)

    def active_pc(self):
        return self.pc_list[self.active]

    def spawn_creatures(self, pcs, mobs):
        i = 0
        for pc, gt in zip(pcs, [(0, 1), (1, 1.5), (-1, 1.5), (2, 2), (-2, 2)]):
            if pc.health > 0:
                pc.set_in_game(self, GameTile(*gt), i / 100)
            i += 2
        i = 1
        for mobdef, gt in mobs:
            c = Creature(mobdef)
            c.set_in_game(self, GameTile(*gt), i / 100)
            i += 2

    def move_pc(self, tile):
        new_tile = self.active_pc.entity.step_to(tile)
        self.creatures[self.active_pc.entity.tile].move_or_attack(new_tile)
        self.new_turn()

    def new_turn(self):
        while True:
            to_act = min(self.creatures.values(), key= lambda x: x.next_action)
            if to_act.is_pc:
                self.active_pc = to_act
                return
            to_act.ai_play()

    def update(self, mouse_pos):
        tile = self.get_tile_for_mouse(mouse_pos)
        cr = self.active_pc
        if tile in self.creatures:
            cr = self.creatures[tile]
        self.hover_display.update(cr)
        #
        for cr in self.creatures.values():
            cr.update()

        for sprite in self.board.values():
            sprite.animate('tiles/Green1.png')

        #Highlight active player
        if self.active_pc:
            self.board[self.active_pc.entity.tile].animate('tiles/Green2.png')

    def is_over(self):
        return all((c.is_pc for c in self.creatures.values())) or all((not c.is_pc for c in self.creatures.values()))

    def erase_all(self):
        for c in self.creatures.values():
            c.erase()
        for tile in self.board.values():
            tile.erase()
        self.hover_display.erase_all()
        self.log_display.erase_all()

    def get_tile_for_mouse(self, mouse_pos):
        for tile, sprite in self.board.items():
            if sprite.rect.collidepoint(mouse_pos):
                return tile

class GameInterface (Interface):
    def __init__ (self, father):
        self.game = Game(father.pc_list, father.mob_list)
        super(GameInterface, self).__init__(father, father.display, 'bg.png', keys=[
            (K_KP4, self.go_sw),
            (K_KP5, self.go_s),
            (K_KP6, self.go_se),
            (K_KP7, self.go_nw),
            (K_KP8, self.go_n),
            (K_KP9, self.go_ne)
            ])



    def on_click(self, mouse_pos):
        pass

    def go_s(self, _):
        self.go(self.game.active_pc.entity.tile.neighbours()[3])

    def go_sw(self, _):
        self.go(self.game.active_pc.entity.tile.neighbours()[4])

    def go_nw(self, _):
        self.go(self.game.active_pc.entity.tile.neighbours()[5])

    def go_n(self, _):
        self.go(self.game.active_pc.entity.tile.neighbours()[0])

    def go_ne(self, _):
        self.go(self.game.active_pc.entity.tile.neighbours()[1])

    def go_se(self, _):
        self.go(self.game.active_pc.entity.tile.neighbours()[2])

    def go(self, tile):
        self.game.move_pc(tile)
        if self.game.is_over():
            self.game.erase_all()
            self.done()
#
    def update(self, mouse_pos):
        self.game.update(mouse_pos)
    

