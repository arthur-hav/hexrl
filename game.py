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

    def cancel(self, key):
        self.done()

    def confirm(self, key):
        exit(0)

class GameTile():
    CO = cos(pi/6)
    MAP_RADIUS = 6.4
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._x = self.x * self.CO
    
    def dist(self, other):
        return sqrt((self._x-other._x)**2 + (self.y-other.y)**2)

    def neighbours(self):
        return [ 
            self + GameTile(-1, 0.5),
            self + GameTile(0, 1), 
            self + GameTile(1, 0.5),
            self + GameTile(-1, -0.5),
            self + GameTile(0, -1), 
            self + GameTile(1, -0.5), 
            ]
    
    def in_boundaries(self):
        return self.dist(GameTile(0,0)) < self.MAP_RADIUS


    def __add__ (self, other):
        """Tiles are vectors and can as well express steps, can be added etc."""
        return GameTile(self.x + other.x, self.y + other.y)

    def __sub__ (self, other):
        return GameTile(self.x - other.x, self.y - other.y)

    def __eq__ (self, other):
        return self.__hash__() == other.__hash__()

    def __str__ (self):
        return "<%s %s>" % (self.x, self.y)

    def __repr__ (self):
        return "<%s %s>" % (self.x, self.y)

    def __hash__ (self):
        return round(2 * self.x) + 100 * round(2 * self.y)

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
                    for tile in current_tile.raycast(current_tile + current_tile - self, go_through):
                        yield tile
                break
        else:
            yield current_tile

    def display_location(self):
        return (340 + 32 * (8 + self.x), 92 + 32 * (7 + self.y))

class HelpInterface(Interface, CascadeElement):
    def __init__(self, father):
        Interface.__init__(self,father, keys = [
            (K_ESCAPE, self.cancel),
            ])
        t = Tooltip()
        t.set_text("""The game mostly plays with numpad. 
Use [4-9] to move or attack adjacent tile.
Use special abilities with numpad [1-3], confirm target with mouse click or [Enter].
[0] to idle for half a turn.
[Esc] to cancel or quit.""")
        self.subsprites = [t]
        self.display()

    def cancel(self, key):
        self.done()

class Tooltip(CascadeElement):
    def __init__(self):
        self.basex, self.basey = 274, 220
        self.bg = SimpleSprite('helpmodal.png')
        self.bg.rect.move_ip(self.basex, self.basey)
        self.subsprites = [self.bg]
    def set_text(self, text):
        self.subsprites = [self.bg]
        for i, line in enumerate(text.split('\n')):
            t = TextSprite(line, '#ffffff', maxlen = 350, x=self.basex + 20, y=self.basey + 20 + 50 * i)
            self.subsprites.append(t)

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
        self.father.game.cursor.animate('icons/target-cursor.png')
    def cancel(self, key):
        self.target = None
        self.father.game.selected = None
        self.done()
    def tab(self, key):
        index = self.valid_targets.index(self.target)
        index = (index + 1) % len(self.valid_targets)
        self.target = self.valid_targets[index]
    def update(self, mouse_pos):
        self.father.game.update(mouse_pos)
        range_hint = self.father.game.get_range_hint(self.father.game.to_act, self.ability)
        for target in range_hint:
            self.father.game.arena.board[target].animate('tiles/GreyTile2.png')
        range_hint = self.father.game.get_splash_hint(self.father.game.to_act, self.ability, self.target)
        for target in range_hint:
            self.father.game.arena.board[target].animate('tiles/Yellow2.png')
        for target in self.valid_targets:
            self.father.game.arena.board[target].animate('tiles/Yellow.png')
        tile = self.father.game.arena.get_tile_for_mouse(mouse_pos)
        if tile and tile in self.valid_targets:
            self.target = tile
        self.father.game.selected = self.target
        self.father.game.display()
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
        self.tooltip = Tooltip()
        self.health = SimpleSprite('icons/heart.png')
        self.health.rect.move_ip(basex + 152, basey + 4)
        self.health_stat = TextSprite('', '#ffffff', basex + 188, basey + 8)
        self.damage = SimpleSprite('icons/sword.png')
        self.damage.rect.move_ip(basex + 228, basey + 4)
        self.damage_stat = TextSprite('', '#ffffff', basex + 264, basey + 8)

        self.armor = SimpleSprite('icons/armor.png')
        self.armor.rect.move_ip(basex + 152, basey + 42)
        self.armor_stat = TextSprite('', '#ffffff', basex + 188, basey + 46)
        self.mr = SimpleSprite('icons/magic-resist.png')
        self.mr.rect.move_ip(basex + 228, basey + 42)
        self.mr_stat = TextSprite('', '#ffffff', basex + 264, basey + 46)

        self.status_effect_display = StatusEffectDisplay(basex + 152, basey + 80)
        self.ability_display = AbilityDisplay(basex, basey + 250)
        self.passive_display = PassiveAbilitiesDisplay(basex, basey + 370)
        self.subsprites = [self.portrait, self.health, self.health_stat, self.damage, self.damage_stat, self.armor, self.armor_stat, self.mr, self.mr_stat, self.description, self.status_effect_display, self.ability_display, self.passive_display]

    def update(self, creature, mouse_pos):
        if self.health.rect.collidepoint(mouse_pos):
            self.tooltip.set_text("Health\nA creature is killed if this reaches 0.")
            if self.tooltip not in self.subsprites:
                self.subsprites.append(self.tooltip)
        elif self.damage.rect.collidepoint(mouse_pos):
            self.tooltip.set_text("Damage\nDamage inflicted per melee attack. Also influences ability damage.")
            if self.tooltip not in self.subsprites:
                self.subsprites.append(self.tooltip)
        elif creature.magic_resist and self.mr.rect.collidepoint(mouse_pos):
            self.tooltip.set_text("Magic resist\nDivides magic damage inflicted by 1 + MR/10.")
            if self.tooltip not in self.subsprites:
                self.subsprites.append(self.tooltip)
        elif creature.armor and self.armor.rect.collidepoint(mouse_pos):
            self.tooltip.set_text("Armor\nDivides physical damage inflicted by 1 + ARM/10.")
            if self.tooltip not in self.subsprites:
                self.subsprites.append(self.tooltip)
        elif self.tooltip in self.subsprites:
            self.subsprites.remove(self.tooltip)
        self.status_effect_display.update(creature, mouse_pos)
        if not creature:
            return
        self.portrait.animate(os.path.join('portraits', creature.portrait))
        self.damage_stat.set_text(str(creature.damage))
        self.health_stat.set_text(str(creature.health))
        self.description.set_text(str(getattr(creature, 'description', '')))
        if creature.magic_resist:
            self.mr_stat.set_text(str(creature.magic_resist))
            if self.mr not in self.subsprites:
                self.subsprites.insert(9, self.mr)
                self.subsprites.insert(9, self.mr_stat)
        elif self.mr in self.subsprites:
            self.subsprites.remove(self.mr)
            self.subsprites.remove(self.mr_stat)
        if creature.armor:
            self.armor_stat.set_text(str(creature.armor))
            if self.armor not in self.subsprites:
                self.subsprites.insert(9, self.armor)
                self.subsprites.insert(9, self.armor_stat)
        elif self.armor in self.subsprites:
            self.subsprites.remove(self.armor)
            self.subsprites.remove(self.armor_stat)
        self.ability_display.update(creature, mouse_pos)
        self.passive_display.update(creature, mouse_pos)

class AbilityDisplay (CascadeElement):
    def __init__ (self, basex, basey):
        super().__init__()
        self.basex = basex
        self.basey = basey
        self.tooltip = Tooltip()
        self.text = TextSprite('Abilities', '#ffffff', basex, basey)
    def update(self, creature, mouse_pos):
        self.subsprites = [self.text]
        for i, ability in enumerate(creature.abilities):
            xoff, yoff = 152 * (i % 2), 40 * (i // 2)
            if creature.ability_cooldown[i]:
                text = '<%d>' % ceil(creature.ability_cooldown[i] / 100)
                image = ability.image_cd
            else:
                text = ability.name
                image = ability.image_name
            key_hint = TextSprite("[%d]" % (i + 1), '#ffffff', self.basex + xoff, self.basey + 24 + yoff)
            sprite = SimpleSprite(image)
            sprite.rect.x, sprite.rect.y = (self.basex + 32 + xoff, self.basey + 20 + yoff)
            if sprite.rect.collidepoint(mouse_pos):
                self.tooltip.set_text("%s\n%s" % (ability.name, ability.description))
                if self.tooltip not in self.subsprites:
                    self.subsprites.append(self.tooltip)
            elif self.tooltip in self.subsprites:
                self.subsprite.remove(self.tooltip)
            text_sprite = TextSprite(text, '#ffffff', self.basex + 70 + xoff, self.basey + 24 + yoff)
            self.subsprites.append(sprite)
            self.subsprites.append(key_hint)
            self.subsprites.append(text_sprite)

class StatusEffectDisplay (CascadeElement):
    def __init__ (self, basex, basey):
        super().__init__()
        self.basex = basex
        self.basey = basey
        self.text = TextSprite('Status effects', '#ffffff', self.basex, self.basey)
        self.tooltip = Tooltip()
    def update(self, creature, mouse_pos):
        #if not creature.status:
        #    self.subsprites = []
        #    return
        self.subsprites = [self.text]
        for i, status in enumerate(creature.status):
            xoff, yoff = 0, 32 * i
            text = '%s <%d>' % (status.name, ceil(creature.status_cooldown[i] / 100))
            text_sprite = TextSprite(text, '#ffffff', self.basex + 38 + xoff, self.basey + 24 + yoff)
            sprite = SimpleSprite(status.image_name)
            sprite.rect.x, sprite.rect.y = (self.basex + xoff, self.basey + 20 + yoff)
            self.subsprites.append(sprite)
            self.subsprites.append(text_sprite)
            if sprite.rect.collidepoint(mouse_pos):
                self.tooltip.set_text("%s\n%s" % (status.name, status.get_description()))
                if self.tooltip not in self.subsprites:
                    self.subsprites.append(self.tooltip)
            elif self.tooltip in self.subsprites:
                self.subsprite.remove(self.tooltip)

class PassiveAbilitiesDisplay (CascadeElement):
    def __init__ (self, basex, basey):
        super().__init__()
        self.basex = basex
        self.basey = basey
        self.text = TextSprite('Passive ability', '#ffffff', self.basex, self.basey)
        self.tooltip = Tooltip()
    def update(self, creature, mouse_pos):
        if not creature.passives:
            self.subsprites = []
            return
        self.subsprites = [self.text]
        for i, passive in enumerate(creature.passives):
            xoff, yoff = 152 * (i % 2), (40 * i // 2)
            text = passive.get_short_desc()
            sprite = SimpleSprite(passive.image_name)
            sprite.rect.x, sprite.rect.y = (self.basex + xoff, self.basey + 20 + yoff)
            self.subsprites.append(sprite)
            text_sprite = TextSprite(text, '#ffffff', self.basex + 38 + xoff, self.basey + 24 + yoff)
            self.subsprites.append(text_sprite)
            if sprite.rect.collidepoint(mouse_pos):
                self.tooltip.set_text("%s\n%s" % (passive.name, passive.get_description()))
                if self.tooltip not in self.subsprites:
                    self.subsprites.append(self.tooltip)
            elif self.tooltip in self.subsprites:
                self.subsprite.remove(self.tooltip)

class LogDisplay (CascadeElement):
    def __init__ (self):
        self.lines = ["", "", "", ""]
        self.line_sprites = [
                TextSprite('', '#999999', 354, 16),
                TextSprite('', '#999999', 354, 32),
                TextSprite('', '#999999', 354, 48),
                TextSprite('', '#ffffff', 354, 64),
            ]
        self.subsprites = self.line_sprites

    def push_text(self, text):
        self.lines.append(text)
        for line, sprite in zip(self.lines[-4:], self.line_sprites):
            sprite.set_text(line)

class DamageLogDisplay (CascadeElement):
    def __init__ (self):
        self.lines = [(None, None, 0)] * 5 
        self.number_sprites = [ TextSprite('', '#ffffff', 848, 138 + 32 * i) for i in range(5) ]
        self.author_sprites = [
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
        ]
        self.mean_sprites = [
            SimpleSprite('icons/sword.png'),
            SimpleSprite('icons/sword.png'),
            SimpleSprite('icons/sword.png'),
            SimpleSprite('icons/sword.png'),
            SimpleSprite('icons/sword.png'),
        ]
        self.basex, self.basey = 780, 132 
        for i in range(5):
            self.author_sprites[i].rect.x = self.basex
            self.author_sprites[i].rect.y = self.basey + 32 * i
            self.mean_sprites[i].rect.x = self.basex + 32 
            self.mean_sprites[i].rect.y = self.basey + 32 * i
        self.subsprites = []
    def update(self):
        self.subsprites = []
        for i, line in enumerate(self.lines):
            if line[0]:
                self.author_sprites[i].animate(line[0])
                self.subsprites.append(self.author_sprites[i]) 
            if line[1]:
                self.mean_sprites[i].animate(line[1])
                self.subsprites.append(self.mean_sprites[i]) 
            if line[2]:
                self.number_sprites[i].set_text(str(line[2]))
                self.subsprites.append(self.number_sprites[i]) 
        self.display()

    def push_line(self, image1, image2, number):
        self.lines.append((image1, image2, number))
        self.lines.pop(0)

class NextToActDisplay (CascadeElement):
    def __init__ (self):
        self.subsprites = []
        self.basex, self.basey = 904, 92

    def update(self, game):
        to_act = sorted(game.creatures.values(), key= lambda x: x.next_action) * 2
        self.subsprites = []
        for actor in to_act[:14]:
            self.subsprites.append(SimpleSprite(actor.image_name))
        for i in range(len(self.subsprites)):
            self.subsprites[i].rect.x = self.basex
            self.subsprites[i].rect.y = self.basey + 32 * i

class StepHint(CascadeElement):
    def __init__(self):
        super().__init__()
        self.subsprites = [TextSprite('[%d]' % (i + 4), '#00FF00', 0, 0) for i in range(6)]
        self.must_display = [False] * 6
        for text in self.subsprites:
            for sprite in text.textsprites:
                sprite.image.set_alpha(120)

    def update(self, creature):
        if not creature.is_pc:
            self.must_display = [False] * 6
            return
        for i, neighbour in enumerate(creature.tile.neighbours()):
            if not neighbour.in_boundaries():
                self.must_display[i] = False
                continue
            self.subsprites[i].textsprites[0].rect.x, self.subsprites[i].textsprites[0].rect.y = neighbour.display_location()
            self.must_display[i] = True

    def display(self):
        for sprite, disp in zip(self.subsprites, self.must_display):
            if disp:
                sprite.display()

class Arena(CascadeElement):
    def __init__(self):
        self.board = {}
        self.step_hints = StepHint()
        for i in range(-8, 8):
            for j in range(-8, 8):
                tile = GameTile(i, j + (i % 2)/2)
                if tile.in_boundaries():
                    self.board[tile] = SimpleSprite('tiles/GreyTile.png')
                    self.board[tile].rect.move_ip(*tile.display_location())
        self.subsprites = list(self.board.values()) + [self.step_hints]

    def update(self, creature, mouse_pos):
        for sprite in self.board.values():
            sprite.animate('tiles/GreyTile.png')

        #Highlight active player
        self.board[creature.tile].animate('tiles/Green2.png')
        self.step_hints.update(creature)

    def get_tile_for_mouse(self, mouse_pos):
        for tile, sprite in self.board.items():
            if sprite.rect.collidepoint(mouse_pos):
                return tile

class HoverXair(SimpleSprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tile = None

    def display(self):
        if not self.tile:
            return
        self.rect.x, self.rect.y = self.tile.display_location()
        super().display()

    def update(self, tile):
        self.tile = tile

class Game(CascadeElement):
    def __init__(self, pc_list, mob_list):
        self.turn = 0
        self.arena = Arena()
        self.creatures = {}
        self.cursor = SimpleSprite('icons/magnifyingglass.png')
        self.hover_display = InfoDisplay(18, 90)
        self.log_display = LogDisplay()
        self.dmg_log_display = DamageLogDisplay()
        self.bg = SimpleSprite('bg.png')
        self.to_act_display = NextToActDisplay()
        self.hover_xair = HoverXair('icons/target.png')
        self.hover_xair.rect.x, self.hover_xair.rect.y = GameTile(0,0).display_location()
        self.selected_xair = HoverXair('icons/select.png')
        self.subsprites = [self.bg, self.arena, self.log_display, self.dmg_log_display, self.to_act_display, self.hover_xair, self.selected_xair, self.cursor]
        #Will be set by new turn, only here declaring
        self.to_act = None
        self.selected = None
        self.spawn_creatures(pc_list, mob_list)
        self.log_display.push_text('Press [?] for help and keybindings')
        self.display()
        self.new_turn()
        self.game_frame = 0

    def spawn_creatures(self, pcs, mobs):
        i = 0
        for pc, gt in zip(pcs, [(-2, 5), (-1, 5.5), (0, 5), (1, 5.5), (2, 5), ]):
            if pc.health > 0:
                pc.set_in_game(self, GameTile(*gt), i)
                self.subsprites.insert(2, pc)
            i += 2
        i = 1
        for mobdef, gt in mobs:
            c = Creature(mobdef)
            c.set_in_game(self, GameTile(*gt), i)
            self.subsprites.insert(2, c)
            i += 2

    def apply_ability(self, ability, creature, target):
        creature.use_ability(ability, target)
        self.new_turn()

    def new_turn(self):
        if self.is_over():
            return
        self.game_frame = 0
        self.selected = None
        to_act = min(self.creatures.values(), key= lambda x: x.next_action)
        if to_act == self.to_act:
            return
        self.to_act = to_act
        elapsed_time = self.to_act.next_action - self.turn
        for creature in list(self.creatures.values()):
            creature.tick(elapsed_time)
        #The creature to act got killed by a dot
        if min(self.creatures.values(), key= lambda x: x.next_action) != self.to_act:
            self.new_turn()
            return
        self.turn = self.to_act.next_action

    def update(self, mouse_pos):
        self.game_frame += 1
        if not self.to_act.is_pc and self.game_frame == 5:
            self.to_act.ai_play()
        elif self.to_act.is_pc:
            self.to_act_display.update(self)
        elif self.game_frame > 10:
            self.new_turn()
        self.cursor.rect.x, self.cursor.rect.y = mouse_pos[0] - 10, mouse_pos[1] - 10 
        tile = self.arena.get_tile_for_mouse(mouse_pos)
        self.hover_xair.update(tile)
        self.selected_xair.update(self.selected)
        creature = self.creatures.get(tile, self.creatures.get(self.selected, self.to_act))
        if creature:
            self.hover_display.update(creature, mouse_pos)
            if self.hover_display not in self.subsprites:
                self.subsprites.insert(7, self.hover_display)
        elif self.hover_display in self.subsprites:
            self.subsprites.remove(self.hover_display)
        #self.dmg_log_display.update()
        for cr in self.creatures.values():
            cr.update()
        self.arena.update(self.to_act, mouse_pos)
        self.display()

    def is_over(self):
        return all((c.is_pc for c in self.creatures.values())) or all((not c.is_pc for c in self.creatures.values()))

    def get_valid_targets(self, creature, ability):
        valid_targets = [tile for tile in self.arena.board.keys() if ability.is_valid_target(creature, tile)]
        return valid_targets

    def get_range_hint(self, creature, ability):
        valid_range = [tile for tile in self.arena.board.keys() if ability.range_hint(creature, tile)]
        return valid_range

    def get_splash_hint(self, creature, ability, selected):
        valid_range = [tile for tile in self.arena.board.keys() if ability.splash_hint(creature, selected, tile)]
        return valid_range


class GameInterface (Interface):
    def __init__ (self, father, mob_list):
        self.game = Game(father.pc_list, mob_list)
        Interface.__init__(self, father, keys=[
            ('[1-3]', self.ability,),
            ('[4-9]', self.go),
            ('0', self.pass_turn),
            ('\?', self.disp_help),
            (K_ESCAPE, self.quit)])


    def on_click(self, mouse_pos):
        pass

    def go(self, code):
        index = int(code) - 4
        if not self.game.to_act or not self.game.to_act.is_pc:
            return
        self.game.to_act.move_or_attack(self.game.to_act.tile.neighbours()[index])
        self.game.new_turn()
        if self.game.is_over():
            self.done()
            return

    def pass_turn(self, _):
        if not self.game.to_act or not self.game.to_act.is_pc:
            return
        self.game.to_act.idle()
        self.game.new_turn()

    def ability(self, key):
        if not self.game.to_act or not self.game.to_act.is_pc:
            return
        if len(self.game.to_act.abilities) < int(key):
            return
        if self.game.to_act.ability_cooldown[int(key) - 1] > 0:
            return
        pc = self.game.to_act
        ability = pc.abilities[int(key) - 1]
        valid_targets = self.game.get_valid_targets(self.game.to_act, ability)
        if not valid_targets:
            self.game.log_display.push_text('No valid target.')
            return
        t = TargetInterface(self, valid_targets, ability)
        t.activate()
        self.desactivate()


    def on_click(self, mouse_pos):
        tile = self.game.arena.get_tile_for_mouse(mouse_pos)
        if self.game.selected and self.game.selected == tile:
            self.selected = None
        self.game.selected = tile

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
            self.game.apply_ability(defunct.ability, self.game.to_act, defunct.target)
        self.game.cursor.animate('icons/magnifyingglass.png')
        if self.game.is_over():
            self.done()
#
    def update(self, mouse_pos):
        self.game.update(mouse_pos)

    def done(self):
        for creature in self.game.creatures.values():
            creature.end_game()
        super().done()
    

