from creatures import Creature
from math import *
from ui import *


class GameTile():
    CO = cos(pi/6)
    MAP_RADIUS = 6.4

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._x = self.x * self.CO
    
    def dist(self, other):
        return sqrt((self._x - other._x)**2 + (self.y - other.y)**2)

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

    def display_location(self):
        return 340 + 32 * (8 + self.x), 92 + 32 * (7 + self.y)


class Arena(CascadeElement):
    def __init__(self):
        super().__init__(self)
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
        # Highlight active player
        self.board[creature.tile].animate('tiles/Green2.png')
        self.step_hints.update(creature)

    def get_tile_for_mouse(self, mouse_pos):
        for tile, sprite in self.board.items():
            if sprite.rect.collidepoint(mouse_pos):
                return tile


class Game(CascadeElement):
    def __init__(self, pc_list, mob_list):
        super().__init__(self)
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
        # Will be set by new turn, only here declaring
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
        # The creature to act got killed by a damage over time
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
        self.selected = None
        Interface.__init__(self, father, keys=[
            ('[1-3]', self.ability,),
            ('[4-9]', self.go),
            ('0', self.pass_turn),
            ('\?', self.disp_help),
            (K_ESCAPE, self.quit)])

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

    def on_return(self, defunct=None):
        if getattr(defunct, 'target', None):
            self.game.apply_ability(defunct.ability, self.game.to_act, defunct.target)
        self.game.cursor.animate('icons/magnifyingglass.png')
        if self.game.is_over():
            self.done()

    def update(self, mouse_pos):
        self.game.update(mouse_pos)

    def done(self):
        for creature in self.game.creatures.values():
            creature.end_game()
        super().done()
    

