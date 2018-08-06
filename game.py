from display import Interface, TextSprite, SimpleSprite, Gauge, CascadeElement
from creatures import Creature
from math import *
from pygame.locals import *
import random
import os.path
import json

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

    def raycast(self, other, go_through = False):
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

    def display_location(self):
        return (208 + 32 * (8 + self.x), 92 + 32 * (7 + self.y))


class TargetInterface(Interface, SimpleSprite):
    def __init__(self, father, valid_targets, handler):
        Interface.__init__(self,father, keys = [
            (K_ESCAPE, self.cancel),
            ])
        SimpleSprite.__init__(self,'icons/target.png')
        self.target = None
        self.valid_targets = valid_targets
        self.handler = handler
    def cancel(self, mouse_pos):
        self.target = None
        self.erase()
        self.done()
    def update(self, mouse_pos):
        tile = self.father.game.arena.get_tile_for_mouse(mouse_pos)
        for target in self.valid_targets:
            self.father.game.arena.board[target].animate('tiles/Yellow.png')
        if tile:
            self.rect.x, self.rect.y = tile.display_location()
            self.display()
        else:
            self.erase()
    def on_click(self, mouse_pos):
        self.target = self.father.game.arena.get_tile_for_mouse(mouse_pos)
        if self.target and self.target in self.valid_targets:
            self.erase()
            self.done()



class InfoDisplay (CascadeElement):
    def __init__ (self, basex, basey):
        self.portrait = SimpleSprite('portraits/Fighter.png')
        self.portrait.rect.x, self.portrait.rect.y = basex, basey
        self.health = SimpleSprite('icons/heart.png')
        self.health.rect.move_ip(basex + 64, basey)
        self.health_stat = TextSprite('', '#ffffff', basex + 100, basey + 6)
        self.damage = SimpleSprite('icons/sword.png')
        self.damage.rect.move_ip(basex + 64, basey + 32)
        self.damage_stat = TextSprite('', '#ffffff', basex + 100, basey + 38)
        self.speed = SimpleSprite('icons/quickness.png')
        self.speed.rect.move_ip(basex + 64, basey + 64)
        self.speed_stat = TextSprite('', '#ffffff', basex + 100, basey + 70)
        self.description = TextSprite('', '#ffffff', basex, basey + 102)
        self.subsprites = [self.portrait, self.health, self.health_stat, self.damage, self.damage_stat, self.speed, self.speed_stat, self.description]

    def update(self, creature):
        if not creature:
            self.erase()
            return
        self.portrait.animate(os.path.join('portraits', creature.portrait))
        self.damage_stat.set_text(str(creature.damage))
        self.health_stat.set_text('%s/%s' % (str(creature.health), str(creature.maxhealth)))
        self.speed_stat.set_text(str(creature.speed))
        self.description.set_text(str(getattr(creature, 'description', '')))
        self.display()

class AbilityDisplay (CascadeElement):
    def update(self, creature):
        self.erase()
        self.subsprites = []
        for ability in creature.abilities:
            sprite = SimpleSprite(ability['image_name'])
            sprite.rect.move_ip(18,450)
            self.subsprites.append(sprite)
        self.display()

class LogDisplay (CascadeElement):
    def __init__ (self):
        self.lines = ["", "", "", ""]
        self.line_sprites = [
                TextSprite('', '#999999', 208, 16),
                TextSprite('', '#999999', 208, 32),
                TextSprite('', '#999999', 208, 48),
                TextSprite('', '#ffffff', 208, 64),
            ]
        self.subsprites = self.line_sprites

    def push_text(self, text):
        self.lines.append(text)
        for line, sprite in zip(self.lines[-4:], self.line_sprites):
            sprite.set_text(line)
            print('push', sprite, sprite.is_displayed)

    def display(self):
        super().display()
        for sprite in self.line_sprites:
            print('disp', sprite, sprite.is_displayed)
    def erase(self):
        super().erase()
        for sprite in self.line_sprites:
            print('erase', sprite.is_displayed)

class Arena(CascadeElement):
    def __init__(self, game):
        self.game = game
        self.board = {}
        for i in range(-10, 10):
            for j in range(-10, 10):
                tile = GameTile(i, j + (i % 2)/2)
                if tile.in_boundaries():
                    self.board[tile] = SimpleSprite('tiles/GreyTile.png')
                    self.board[tile].rect.move_ip(*tile.display_location())
        self.subsprites = list(self.board.values())

    def update(self, mouse_pos):
        for sprite in self.board.values():
            sprite.animate('tiles/GreyTile.png')

        #Highlight active player
        if self.game.active_pc:
            self.board[self.game.active_pc.tile].animate('tiles/Green2.png')

    def get_tile_for_mouse(self, mouse_pos):
        for tile, sprite in self.board.items():
            if sprite.rect.collidepoint(mouse_pos):
                return tile

class Game(CascadeElement):
    def __init__(self, pc_list, mob_list):
        self.turn = 0
        self.arena = Arena(self)
        self.creatures = {}
        self.hover_display = InfoDisplay(18, 90)
        self.active_display = InfoDisplay(18, 340)
        self.log_display = LogDisplay()
        self.ability_display = AbilityDisplay()
        self.bg = SimpleSprite('bg.png')
        self.subsprites = [self.bg, self.hover_display, self.ability_display, self.active_display, self.log_display, self.arena]
        #Will be set by new turn, only here declaring
        self.active_pc = None
        self.spawn_creatures(pc_list, mob_list)
        self.display()
        self.new_turn()

    def get_valid_targets(self, creature, ability):
        valid_targets = [tile for tile in self.arena.board.keys() if ability.is_valid_target(creature, tile)]
        return valid_targets

    def spawn_creatures(self, pcs, mobs):
        i = 0
        for pc, gt in zip(pcs, [(0, 6), (1, 6.5), (-1, 6.5), (2, 6), (-2, 6)]):
            if pc.health > 0:
                pc.set_in_game(self, GameTile(*gt), i / 100)
                self.subsprites.append(pc)
            i += 2
        i = 1
        for mobdef, gt in mobs:
            c = Creature(mobdef)
            c.set_in_game(self, GameTile(*gt), i / 100)
            self.subsprites.append(c)
            i += 2

    def move_pc(self, tile):
        self.creatures[self.active_pc.tile].move_or_attack(tile)
        self.new_turn()

    def new_turn(self):
        while True:
            to_act = min(self.creatures.values(), key= lambda x: x.next_action)
            if to_act.is_pc:
                self.active_pc = to_act
                self.active_display.update(to_act)
                self.ability_display.update(to_act)
                return
            if self.is_over():
                break
            to_act.ai_play()

    def update(self, mouse_pos):
        tile = self.arena.get_tile_for_mouse(mouse_pos)
        cr = self.creatures.get(tile, None)
        self.hover_display.update(cr)
        #
        for cr in self.creatures.values():
            cr.update()
        self.arena.update(mouse_pos)

    def is_over(self):
        return all((c.is_pc for c in self.creatures.values())) or all((not c.is_pc for c in self.creatures.values()))


class GameInterface (Interface):
    def __init__ (self, father):
        self.game = Game(father.pc_list, father.mob_list)
        Interface.__init__(self, father, keys=[
            (K_KP1, self.ability_one,),
            (K_KP2, self.ability_two,),
            (K_KP3, self.ability_three,),
            (K_KP4, self.go_sw),
            (K_KP5, self.go_s),
            (K_KP6, self.go_se),
            (K_KP7, self.go_nw),
            (K_KP8, self.go_n),
            (K_KP9, self.go_ne),
            (K_ESCAPE, self.quit)])


    def on_click(self, mouse_pos):
        pass

    def go_s(self, _):
        self.go(self.game.active_pc.tile.neighbours()[3])

    def go_sw(self, _):
        self.go(self.game.active_pc.tile.neighbours()[4])

    def go_nw(self, _):
        self.go(self.game.active_pc.tile.neighbours()[5])

    def go_n(self, _):
        self.go(self.game.active_pc.tile.neighbours()[0])

    def go_ne(self, _):
        self.go(self.game.active_pc.tile.neighbours()[1])

    def go_se(self, _):
        self.go(self.game.active_pc.tile.neighbours()[2])

    def go(self, tile):
        self.game.move_pc(tile)
        if self.game.is_over():
            self.game.erase()
            self.done()

    def ability_one(self, mouse_pos):
        if len(self.game.active_pc.abilities) < 1:
            return
        pc = self.game.active_pc
        self._ability(pc, pc.abilities[0]['handler'])

    def ability_two(self, mouse_pos):
        if len(self.game.active_pc.abilities) < 2:
            return
        pc = self.game.active_pc
        self._ability(pc, pc.abilities[1]['handler'])

    def ability_three(self, mouse_pos):
        if len(self.game.active_pc.abilities) < 3:
            return
        pc = self.game.active_pc
        self._ability(pc, pc.abilities[2]['handler'])

    def _ability(self, pc, handler):
        valid_targets = self.game.get_valid_targets(pc, handler)
        if not valid_targets:
            self.game.log_display.push_text('No valid target.')
            return
        if valid_targets != [pc.tile]:
            t = TargetInterface(self, valid_targets, handler)
            t.activate()
            self.desactivate()
        else:
            time_spent = handler.apply_ability(self.game.active_pc, self.game.active_pc.tile)
            self.game.active_pc.next_action += time_spent / self.game.active_pc.speed
            self.game.new_turn()


    def quit(self, _):
        exit(0)

    def on_return(self, defunct):
        if defunct.target:
            time_spent = defunct.handler.apply_ability(self.game.active_pc, defunct.target)
            self.game.active_pc.next_action += time_spent / self.game.active_pc.speed
            self.game.new_turn()
#
    def update(self, mouse_pos):
        self.game.update(mouse_pos)
    

