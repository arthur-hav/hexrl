from display import Interface, TextSprite, SimpleSprite, Gauge, CascadeElement
from creatures import Creature
from math import *
from pygame.locals import *
import random
import os.path
import json

class QuitInterface(Interface, CascadeElement):
    def __init__(self, father):
        Interface.__init__(self,father, keys = [
            (K_ESCAPE, self.cancel),
            ('y', self.confirm),
            ('n', self.cancel),
            ])
        text = 'Really quit ? [y] / [n]'
        basex, basey = 274, 220
        bg = SimpleSprite('helpmodal.png')
        bg.rect.move_ip(basex, basey)
        t1 = TextSprite(text, '#ffffff', maxlen = 350, x=basex + 20, y=basey + 100)
        self.subsprites = [bg, t1]
        self.display()

    def cancel(self, mouse_pos):
        self.erase()
        self.done()

    def confirm(self, mouse_pos):
        exit(0)

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

class HelpInterface(Interface, CascadeElement):
    def __init__(self, father):
        Interface.__init__(self,father, keys = [
            (K_ESCAPE, self.cancel),
            ])
        text1 = 'Move your adventurers with numpad [4-9] (4 goes southwest, 5 goes south etc.)'
        text2 = 'Use special abilities with numpad [1-3], confirm target with mouse click or [Enter].'
        text3 = '[0] idle for half a turn.'
        text4 = '[Escape] to cancel or quit.'
        basex, basey = 274, 220
        bg = SimpleSprite('helpmodal.png')
        bg.rect.move_ip(basex, basey)
        t1 = TextSprite(text1, '#ffffff', maxlen = 350, x=basex + 20, y=basey + 20)
        t2 = TextSprite(text2, '#ffffff', maxlen = 350, x=basex + 20, y=basey + 70)
        t3 = TextSprite(text3, '#ffffff', maxlen = 350, x=basex + 20, y=basey + 120)
        t4 = TextSprite(text3, '#ffffff', maxlen = 350, x=basex + 20, y=basey + 170)
        self.subsprites = [bg, t1, t2, t3]
        self.display()

    def cancel(self, mouse_pos):
        self.erase()
        self.done()


class TargetInterface(Interface):
    def __init__(self, father, valid_targets, ability):
        super().__init__(father, keys = [
            (K_ESCAPE, self.cancel),
            (K_RETURN, self.confirm),
            (K_TAB, self.tab),
            ])
        self.target = self.father.game.selected if self.father.game.selected \
            and self.father.game.selected in valid_targets else valid_targets[0]
        self.valid_targets = valid_targets
        self.ability = ability
    def cancel(self, mouse_pos):
        self.target = None
        self.father.game.selected = None
        self.done()
    def tab(self, mouse_pos):
        index = self.valid_targets.index(self.target)
        index = (index + 1) % len(self.valid_targets)
        self.target = self.valid_targets[index]
    def update(self, mouse_pos):
        self.father.game.update(mouse_pos)
        range_hint = self.father.game.get_range_hint(self.father.game.active_pc, self.ability)
        for target in range_hint:
            self.father.game.arena.board[target].animate('tiles/Yellow2.png')
        for target in self.valid_targets:
            self.father.game.arena.board[target].animate('tiles/Yellow.png')
        tile = self.father.game.arena.get_tile_for_mouse(mouse_pos)
        if tile and tile in self.valid_targets:
            self.target = tile
        self.father.game.selected = self.target
    def on_click(self, mouse_pos):
        self.target = self.father.game.arena.get_tile_for_mouse(mouse_pos)
        if self.target and self.target in self.valid_targets:
            self.father.game.selected = None
            self.done()
    def confirm(self, mouse_pos):
        self.father.game.selected = None
        self.done()

class InfoDisplay (CascadeElement):
    def __init__ (self, basex, basey):
        self.portrait = SimpleSprite('portraits/Fighter.png')
        self.portrait.rect.x, self.portrait.rect.y = basex, basey

        self.description = TextSprite('', '#ffffff', basex, basey + 192, maxlen=120)

        self.health = SimpleSprite('icons/heart.png')
        self.health.rect.move_ip(basex, basey + 224)
        self.health_stat = TextSprite('', '#ffffff', basex + 36, basey + 228)
        self.damage = SimpleSprite('icons/sword.png')
        self.damage.rect.move_ip(basex, basey + 256)
        self.damage_stat = TextSprite('', '#ffffff', basex + 36, basey + 260)
        self.speed = SimpleSprite('icons/quickness.png')
        self.speed.rect.move_ip(basex + 80, basey + 256) 
        self.speed_stat = TextSprite('', '#ffffff', basex + 116, basey + 260)
        self.ability_display = AbilityDisplay(basex, basey + 288)
        self.subsprites = [self.portrait, self.health, self.health_stat, self.damage, self.damage_stat, self.speed, self.speed_stat, self.description]

    def update(self, creature):
        self.ability_display.update(creature)
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
    def __init__ (self, basex, basey):
        super().__init__()
        self.basex = basex
        self.basey = basey
    def update(self, creature):
        self.erase()
        self.subsprites = []
        for i, ability in enumerate(creature.abilities):
            ability.rect.x, ability.rect.y = (self.basex , self.basey + 32 * i)
            if creature.ability_cooldown[i]:
                text = '<Wait %d turn(s)>' % ceil(creature.ability_cooldown[i] / 100)
                ability.animate(ability.image_cd)
            else:
                text = ability.name
                ability.animate(ability.image_name)
            self.subsprites.append(ability)
            text_sprite = TextSprite(text, '#ffffff', self.basex + 38, self.basey + 4 + 32 * i)
            self.subsprites.append(text_sprite)
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

class NextToActDisplay (CascadeElement):
    def __init__ (self):
        self.subsprites = [
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
        ]
        self.basex, self.basey = 780, 92
        for i in range(4):
            self.subsprites[i].rect.x = self.basex + 32 * i
            self.subsprites[i].rect.y = self.basey

    def update(self, game):
        to_act = sorted(game.creatures.values(), key= lambda x: x.next_action) * 4
        for i in range(4):
            self.subsprites[i].animate(to_act[i].image_name)


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

        #Highlight creatures
        for creature in self.game.creatures.values():
            self.board[creature.tile].animate('tiles/GreyTile2.png' if creature.is_pc else 'tiles/Red1.png')
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
        #self.active_display = InfoDisplay(18, 340)
        self.log_display = LogDisplay()
        self.bg = SimpleSprite('bg.png')
        self.to_act_display = NextToActDisplay()
        self.hover_xair = SimpleSprite('icons/target.png')
        self.selected_xair = SimpleSprite('icons/select.png')
        self.subsprites = [self.bg, self.hover_display, self.log_display, self.arena, self.to_act_display, self.hover_xair, self.selected_xair]
        #Will be set by new turn, only here declaring
        self.active_pc = None
        self.selected = None
        self.spawn_creatures(pc_list, mob_list)
        self.log_display.push_text('Press <?> for help and keybindings')
        self.display()
        self.new_turn()

    def spawn_creatures(self, pcs, mobs):
        i = 0
        for pc, gt in zip(pcs, [(0, 6), (1, 6.5), (-1, 6.5), (2, 6), (-2, 6)]):
            if pc.health > 0:
                pc.set_in_game(self, GameTile(*gt), i)
                self.subsprites.append(pc)
            i += 2
        i = 1
        for mobdef, gt in mobs:
            c = Creature(mobdef)
            c.set_in_game(self, GameTile(*gt), i)
            self.subsprites.append(c)
            i += 2

    def move_pc(self, tile):
        self.creatures[self.active_pc.tile].move_or_attack(tile)

    def apply_ability(self, ability, creature, target):
        creature.use_ability(ability, target)

    def new_turn(self):
        self.selected = None
        while not self.is_over():
            self.to_act_display.update(self)
            to_act = min(self.creatures.values(), key= lambda x: x.next_action)
            elapsed_time = to_act.next_action - self.turn
            for creature in self.creatures.values():
                creature.tick(elapsed_time)
            self.turn = to_act.next_action
            if not to_act.is_pc:
                to_act.ai_play()
            else:
                self.active_pc = to_act
                break

    def update(self, mouse_pos):
        tile = self.arena.get_tile_for_mouse(mouse_pos)
        cr = self.creatures.get(tile, self.creatures.get(self.selected, self.active_pc))
        self.hover_display.update(cr)
        for cr in self.creatures.values():
            cr.update()
        self.arena.update(mouse_pos)
        if tile:
            self.hover_xair.rect.x, self.hover_xair.rect.y = tile.display_location()
            self.hover_xair.display()
        else:
            self.hover_xair.erase()
        if self.selected:
            self.selected_xair.rect.x, self.selected_xair.rect.y = self.selected.display_location()
            self.selected_xair.display()
        else:
            self.selected_xair.erase()

    def is_over(self):
        return all((c.is_pc for c in self.creatures.values())) or all((not c.is_pc for c in self.creatures.values()))

    def get_valid_targets(self, creature, ability):
        valid_targets = [tile for tile in self.arena.board.keys() if ability.is_valid_target(creature, tile)]
        return valid_targets

    def get_range_hint(self, creature, ability):
        valid_range = [tile for tile in self.arena.board.keys() if ability.range_hint(creature, tile)]
        return valid_range


class GameInterface (Interface):
    def __init__ (self, father, mob_list):
        self.game = Game(father.pc_list, mob_list)
        Interface.__init__(self, father, keys=[
            ('1', self.ability_one,),
            ('2', self.ability_two,),
            ('3', self.ability_three,),
            ('4', self.go_sw),
            ('5', self.go_s),
            ('6', self.go_se),
            ('7', self.go_nw),
            ('8', self.go_n),
            ('9', self.go_ne),
            ('0', self.pass_turn),
            ('?', self.disp_help),
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

    def pass_turn(self, _):
        self.game.active_pc.next_action += 50
        self.game.new_turn()

    def ability_one(self, mouse_pos):
        if len(self.game.active_pc.abilities) < 1:
            return
        if self.game.active_pc.ability_cooldown[0] > 0:
            return
        pc = self.game.active_pc
        self._ability(pc, pc.abilities[0])

    def ability_two(self, mouse_pos):
        if len(self.game.active_pc.abilities) < 2:
            return
        if self.game.active_pc.ability_cooldown[1] > 0:
            return
        pc = self.game.active_pc
        self._ability(pc, pc.abilities[1])

    def ability_three(self, mouse_pos):
        if len(self.game.active_pc.abilities) < 3:
            return
        if self.game.active_pc.ability_cooldown[2] > 0:
            return
        pc = self.game.active_pc
        self._ability(pc, pc.abilities[2])

    def on_click(self, mouse_pos):
        tile = self.game.arena.get_tile_for_mouse(mouse_pos)
        if self.game.selected and self.game.selected == tile:
            self.selected = None
        self.game.selected = tile

    def _ability(self, pc, ability):
        valid_targets = self.game.get_valid_targets(self.game.active_pc, ability)
        if not valid_targets:
            self.game.log_display.push_text('No valid target.')
            return
        t = TargetInterface(self, valid_targets, ability)
        t.activate()
        self.desactivate()

    def quit(self, _):
        qi = QuitInterface(self)
        qi.activate()
        self.desactivate()

    def disp_help(self, _):
        hi = HelpInterface(self)
        hi.activate()
        self.desactivate()

    def on_return(self, defunct):
        if getattr(defunct, 'target', None):
            self.game.apply_ability(defunct.ability, self.game.active_pc, defunct.target)
#
    def update(self, mouse_pos):
        self.game.update(mouse_pos)
    

