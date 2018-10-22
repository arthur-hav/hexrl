from creatures import Creature
from combat_ui import *
from gametile import GameTile
import random


class Combat(CascadeElement):
    MAP_RADIUS = 6.4
    def __init__(self, pc_list, mob_list):
        super().__init__()
        self.creatures = {}
        self.turn = 0
        self.to_act = None
        self.selected = None
        self.new_turn()
        self.subsprites = []
        self.spawn_creatures(pc_list, mob_list)

    def spawn_creatures(self, pcs, mobs):
        i = 0
        for pc, gt in pcs:
            if pc.health > 0:
                pc.set_in_combat(self, GameTile(*gt), i)
            i += 2
        i = 1
        mob_zone = [gt for gt in GameTile.all_tiles(self.MAP_RADIUS) if gt.y < -3.25]
        for mobdef in mobs:
            gt = random.choice(mob_zone)
            mob_zone.remove(gt)
            c = Creature(mobdef)
            c.set_in_combat(self, gt, i)
            i += 2

    def new_turn(self):
        if self.is_over():
            return
        to_act = min(self.creatures.values(), key=lambda x: x.next_action)
        if to_act == self.to_act:
            return
        self.to_act = to_act
        elapsed_time = self.to_act.next_action - self.turn
        for creature in list(self.creatures.values()):
            creature.tick(elapsed_time)
        # The creature to act got killed by a damage over time
        if min(self.creatures.values(), key=lambda x: x.next_action) != self.to_act:
            self.new_turn()
            return
        self.turn = self.to_act.next_action

    def is_over(self):
        return all((c.is_pc for c in self.creatures.values())) or all((not c.is_pc for c in self.creatures.values()))

    def get_valid_targets(self, creature, ability):
        valid_targets = [tile for tile in GameTile.all_tiles(self.MAP_RADIUS) if ability.is_valid_target(creature, tile)]
        return valid_targets

    def get_range_hint(self, creature, ability):
        valid_range = [tile for tile in GameTile.all_tiles(self.MAP_RADIUS) if ability.range_hint(creature, tile)]
        return valid_range

    def get_splash_hint(self, creature, ability, selected):
        valid_range = [tile for tile in GameTile.all_tiles(self.MAP_RADIUS) if ability.splash_hint(creature, selected, tile)]
        return valid_range
    
    def apply_ability(self, ability, creature, target):
        creature.use_ability(ability, target)
        self.new_turn()
    
    def update(self):
        for cr in self.creatures.values():
            cr.update()


class CombatInterface (Interface):
    def __init__ (self, father, mob_list):
        self.combat = Combat(zip(father.pc_list, father.formation), mob_list)
        self.combat.new_turn()
        self.combat_ui = GameUI(self.combat)
        self.selected = None
        super().__init__(father, keys=[
            ('[1-3]', self.ability,),
            ('(up|down)(left|right)?', self.go),
            ('0', self.pass_turn),
            ('\?', self.disp_help),
            (K_ESCAPE, self.quit)])

    def go(self, code):
        if not self.combat.to_act or not self.combat.to_act.is_pc:
            return
        moves = {
            'down': 1,
            'downleft': 0,
            'downright': 2,
            'up': 4,
            'upright': 5,
            'upleft': 3
        }
        index = moves[code]
        self.combat.to_act.move_or_attack(self.combat.to_act.tile.neighbours()[index])
        self.combat.new_turn()
        if self.combat.is_over():
            self.done()
            return

    def pass_turn(self, _):
        if not self.combat.to_act or not self.combat.to_act.is_pc:
            return
        self.combat.to_act.idle()
        self.combat.new_turn()

    def ability(self, key):
        if not self.combat.to_act or not self.combat.to_act.is_pc:
            return
        if len(self.combat.to_act.abilities) < int(key):
            self.combat_ui.log_display.push_text('Unknown ability')
            return
        if self.combat.to_act.silenced:
            self.combat_ui.log_display.push_text('Not while silenced !')
            return
        if self.combat.to_act.abilities[int(key) - 1].current_cooldown > 0:
            self.combat_ui.log_display.push_text('Ability is currently in cooldown')
            return
        pc = self.combat.to_act
        ability = pc.abilities[int(key) - 1]
        valid_targets = self.combat.get_valid_targets(self.combat.to_act, ability)
        if not valid_targets:
            self.combat_ui.log_display.push_text('No valid target.')
            return
        t = TargetInterface(self, valid_targets, ability)
        t.activate()
        self.desactivate()

    def on_click(self, mouse_pos):
        tile = GameTile.get_tile_for_mouse(mouse_pos)
        if self.combat.selected and self.combat.selected == tile:
            self.combat.selected = None
        else:
            self.combat.selected = tile

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
            self.combat.apply_ability(defunct.ability, self.combat.to_act, defunct.target)
        self.combat_ui.cursor.animate('icons/magnifyingglass.png')
        if self.combat.is_over():
            self.done()

    def update(self, mouse_pos):
        if self.combat.is_over():
            self.done()
            return
        self.combat_ui.to_act_display.update(self.combat)
        if not self.combat.to_act.is_pc and self.combat_ui.game_frame == 5:
            self.combat.to_act.ai_play()
        elif self.combat_ui.game_frame > 10:
            self.combat.new_turn()
            self.combat_ui.game_frame = 0

        self.combat.update()
        self.combat_ui.update(self.combat, mouse_pos)

        self.combat_ui.display()

    def done(self):
        for creature in self.combat.creatures.values():
            creature.end_combat()
        super().done()
    

