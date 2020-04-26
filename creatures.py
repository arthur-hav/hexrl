from display import SimpleSprite, CascadeElement, Gauge
from abilities import ABILITIES
from passives import PASSIVES
from items import ITEMS
import random
import math


class SideHealthGauge(Gauge):
    def __init__(self, creature):
        self.creature = creature
        super().__init__(4, 32, '#BB0008')

    def update(self):
        self.height = math.ceil((16 * self.creature.health) / self.creature.maxhealth) * 2
        self.rect.x, self.rect.y = self.creature.tile.display_location()
        self.rect.y += 32 - self.height
        self.set_height(self.height)
        if self.creature.health == self.creature.maxhealth:
            self.set_height(0)


class SideShieldGauge(Gauge):
    def __init__(self, creature):
        self.creature = creature
        super().__init__(4, 32, '#BBCCFF')

    def update(self):
        self.height = math.ceil((16 * self.creature.shield) / self.creature.maxhealth) * 2
        self.rect.x, self.rect.y = self.creature.tile.display_location()
        self.rect.y += 32 - self.height
        self.set_height(self.height)


class Creature(SimpleSprite, CascadeElement):

    def __init__(self, defkey, is_pc=False):
        CascadeElement.__init__(self)
        self.attack_range = 1
        self.health = 0
        self.maxhealth = 0
        self.damage = 0
        self.armor = 0
        self.magic_resist = 0
        self.passives = []
        self.status = []
        self.abilities = []
        self.items = []
        self.rooted = []
        self.silenced = []
        self.frames = []
        self.tile = None
        self.combat = None
        self.moving_from = None
        self.next_action = None
        self.moving_frame = 0
        self.shield = 0
        self.is_pc = is_pc
        self.defkey = defkey
        self.health_gauge = SideHealthGauge(self)
        self.shield_gauge = SideShieldGauge(self)
        self.load_def(defkey)

    def load_def(self, defkey):
        for k, v in DEFS[defkey].items():
            setattr(self, k, v)
        creature_passive_def = [k[1] for k in self.passives]
        self.passives = [PASSIVES[k[0]] for k in self.passives]
        for c_def, passive_template in zip(creature_passive_def, self.passives):
            c_def.update(passive_template[1])
        self.passives = [template[0](**c_def) for template, c_def in zip(self.passives, creature_passive_def)]
        for passive in self.passives:
            passive.apply_to(self)
        creature_ability_def = [k[1] for k in self.abilities]
        self.abilities = [ABILITIES[k[0]] for k in self.abilities]
        for c_def, ability_template in zip(creature_ability_def, self.abilities):
            c_def.update(ability_template[1])
        self.abilities = [template[0](**c_def) for template, c_def in zip(self.abilities, creature_ability_def)]
        self.maxhealth = self.health
        SimpleSprite.__init__(self, DEFS[defkey]['image_name'])
        self.subsprites = [self.health_gauge, self.shield_gauge]

    def set_in_combat(self, combat, game_tile, next_action):
        self.tile = game_tile
        self.rect.x, self.rect.y = self.tile.display_location()
        self.combat = combat
        self.combat.creatures[game_tile] = self
        self.next_action = next_action
        self.shield = 0
        self.status = []

    def end_combat(self):
        for status in self.status:
            status.status_end(self)
        for ability in self.abilities:
            ability.current_cooldown = 0
        self.status = []
        self.combat = None
        self.tile = None

    def update(self):
        if self.moving_from:
            self.moving_frame += 1
            old_x, old_y = self.moving_from.display_location()
            new_x, new_y = self.tile.display_location()
            self.move_to(old_x + (new_x - old_x) * self.moving_frame / 3,
                         old_y + (new_y - old_y) * self.moving_frame / 3)
            if self.moving_frame >= 3:
                self.moving_from = None
                self.moving_frame = 0
        if self.frames:
            self.animate(self.frames.pop(0))
        self.health_gauge.update()
        self.shield_gauge.update()

    def dict_dump(self):
        items = self.items.copy()
        # This is so we dont stack stats by saving/loading with, say, a health amulet
        for item in items:
            item.unequip()
        d = {
            'items': [item.name for item in items],
            'health': self.health,
            'maxhealth': self.maxhealth,
            'damage': self.damage,
            'defkey': self.defkey
        }
        for item in items:
            item.equip(self)
        return d

    @staticmethod
    def dict_load(data, items):
        c = Creature(data['defkey'])
        c.health = data['health']
        if 'damage' in data:
            c.damage = data['damage']
        if 'maxhealth' in data:
            c.maxhealth = data['maxhealth']
        for key in data['items']:
            item_class = ITEMS[key][0]
            item_args = ITEMS[key][1]
            item = item_class(*item_args)
            item.equip(c)
        c.is_pc = True
        return c

    # Below this : only valid if previously set_in_combat

    def tick(self, elapsed_time):
        for ability in self.abilities:
            ability.tick(self, elapsed_time)
        for status in self.status.copy():
            status.tick(self, elapsed_time)

    def step_to(self, target):
        return min(self.tile.neighbours(), key=lambda x: x.dist(target))

    def step_away(self, target):
        try:
            return max([t for t in self.tile.neighbours() if t not in self.combat.creatures],
                       key=lambda x: x.dist(target))
        except ValueError:
            return None

    def move_or_attack(self, destination):
        if not destination.in_boundaries(self.combat.MAP_RADIUS):
            return
        if destination in self.combat.creatures and self.is_pc != self.combat.creatures[destination].is_pc:
            return self.attack(destination)
        elif self.rooted:
            return
        elif destination in self.combat.creatures:
            # Swap places
            other_cr = self.combat.creatures[destination]
            other_cr.moving_from = other_cr.tile
            other_cr.tile = self.tile
            other_cr.combat.creatures[self.tile] = other_cr
            del self.combat.creatures[destination]
        else:
            del self.combat.creatures[self.tile]
        self.moving_from = self.tile
        self.tile = destination
        self.combat.creatures[destination] = self
        self.end_act()

    def idle(self):
        self.end_act()

    def end_act(self):
        self.next_action += 100

    def attack(self, destination):
        creature = self.combat.creatures[destination]
        creature.take_damage(self.damage)
        # self.game.dmg_log_display.push_line(self.image_name, 'icons/sword.png', self.damage)
        self.end_act()

    def use_ability(self, ability, target):
        if self.silenced:
            return
        ability.apply_ability(self, target)
        if not ability.is_instant:
            self.end_act()

    def add_status(self, status_effect):
        for status in self.status:
            if status.name == status_effect.name:
                status.duration = max(status_effect.duration, status.duration)
                return
        self.status.append(status_effect)
        status_effect.status_start(self)

    def take_damage(self, number, dmg_type='physical'):
        if dmg_type == 'physical' and self.armor > 0:
            number = round(10 * number / (10 + self.armor))
        elif dmg_type == 'magic' and self.magic_resist > 0:
            number = round(10 * number / (10 + self.magic_resist))
        if self.shield:
            self.shield -= number
            if self.shield < 0:
                self.health += self.shield
                self.shield = 0
        else:
            self.health -= number
        self.frames.extend(['tiles/Hit.png', self.image_name])
        if self.health <= 0:
            for status in self.status:
                status.status_end(self)
            self.status = []
            self.passives = []
            # self.game.log_display.push_text("%s dies." % (self.name))
            del self.combat.creatures[self.tile]
            self.must_show = False

    def ai_play(self, is_pc):
        nearest_ennemy = min([c for c in self.combat.creatures.values() if c.is_pc != is_pc and c.health > 0],
                             key=lambda x: x.tile.dist(self.tile))
        # CASTING
        if self.abilities and not self.silenced:
            ability = random.choice(self.abilities)
            if ability.current_cooldown == 0:
                target = ability.get_ai_valid_target(self)
                if target:
                    self.use_ability(ability, target)
                    return

        # FLEEING
        if self.attack_range > 1 and self.tile.dist(nearest_ennemy.tile) < 2.25:
            tile = self.step_away(nearest_ennemy.tile)
            if tile and tile.in_boundaries(self.combat.MAP_RADIUS) and not self.rooted:
                self.move_or_attack(tile)
                return
        # HUNTING
        if (not self.rooted or nearest_ennemy.tile.dist(self.tile) < 1.25) and (
                self.attack_range == 1 or nearest_ennemy.tile.dist(self.tile) > self.attack_range):
            if nearest_ennemy.tile.dist(self.tile) <= self.attack_range:
                self.attack(nearest_ennemy.tile)
                return
            tile = self.step_to(nearest_ennemy.tile)
            # Only swap position with a lesser hp ally to avoid dancing
            if tile not in self.combat.creatures or self.combat.creatures[tile].is_pc != self.is_pc or \
                    self.combat.creatures[tile].health < self.health:
                self.move_or_attack(tile)
                return
        # IDLE
        self.idle()

    def display(self):
        if self.combat:
            CascadeElement.display(self)
        SimpleSprite.display(self)


DEFS = {
    'Fighter': {
        'portrait': 'portraits/Fighter.png',
        'image_name': 'tiles/Fighter.png',
        'health': 100,
        'damage': 14,
        'armor': 2,
        'magic_resist': 1,
        'attack_range': 1,
        'name': 'Fighter',
        'abilities': [
            ('Smite', {'ability_range': 2, 'power': 16, 'health_cost': 2, 'cooldown': 300, 'need_los': False, }),
        ],
        'passives': [
            ('Shield', {'shield': 5}),
        ]
    },
    'Barbarian': {
        'portrait': 'portraits/Barbarian.png',
        'image_name': 'tiles/Barbarian.png',
        'health': 90,
        'damage': 16,
        'armor': 1,
        'magic_resist': 1,
        'attack_range': 1,
        'name': 'Barbarian',
        'passives': [('Regeneration', {'rate': 2, 'maxhealth': 25})],
        'abilities': [('Cleave', {'ability_range': 1, 'power': 16, 'cooldown': 200})]
    },
    'Archer': {
        'portrait': 'portraits/Archer.png',
        'image_name': 'tiles/Archer.png',
        'health': 60,
        'damage': 12,
        'attack_range': 4,
        'name': 'Archer',
        'passives': [],
        'abilities': [],
    },
    'Wizard': {
        'portrait': 'portraits/Wizard.png',
        'image_name': 'tiles/Wizard.png',
        'health': 50,
        'damage': 10,
        'attack_range': 3,
        'name': 'Wizard',
        'passives': [('Fastcast', {})],
        'abilities': [('Fireball', {'ability_range': 3, 'power': 15, 'aoe': 0.75, 'need_los': True, 'cooldown': 200})],
    },
    'Enchantress': {
        'portrait': 'portraits/Elf.png',
        'image_name': 'tiles/Elf.png',
        'health': 50,
        'damage': 10,
        'attack_range': 3,
        'name': 'Enchantress',
        'passives': [('PartyHeal', {'amount': 5})],
        'abilities': [('Root', {'ability_range': 4, 'cooldown': 200, 'duration': 300, 'need_los': True})],
    },

    'Gobelin': {
        'portrait': 'portraits/Gobelin.png',
        'image_name': 'tiles/Gobelin.png',
        'health': 50,
        'damage': 8,
        'name': 'Gobelin',
        'passives': [('Quick', {'bonus_moves': 2})],
        'abilities': [],
    },
    'Troll': {
        'portrait': 'portraits/Gobelin.png',
        'image_name': 'tiles/Troll.png',
        'health': 70,
        'armor': 3,
        'damage': 12,
        'name': 'Troll',
        'abilities': [],
        'passives': [('Regeneration', {'rate': 6, 'maxhealth': None})]
    },
    'Skeleton': {
        'portrait': 'portraits/Skeleton.png',
        'image_name': 'tiles/Skeleton.png',
        'description': 'Dangerous in great numbers.',
        'health': 60,
        'damage': 7,
        'name': 'Skeleton',
        'abilities': [],
    },
    'SkeletonArcher': {
        'portrait': 'portraits/Skeleton.png',
        'image_name': 'tiles/SkeletonArcher.png',
        'description': 'Ranged',
        'health': 50,
        'attack_range': 3,
        'damage': 5,
        'name': 'Skeleton Archer',
        'abilities': [],
    },
    'Necromancer': {
        'portrait': 'portraits/Necromancer.png',
        'image_name': 'tiles/Necromancer.png',
        'health': 70,
        'damage': 7,
        'name': 'Necromancer',
        'attack_range': 3,
        'description': 'Can raise undead',
        'abilities': [('Raise Undead', {'ability_range': 2, 'cooldown': 300, })],
    },
    'Demon': {
        'portrait': 'portraits/Demon.png',
        'image_name': 'tiles/Demon.png',
        'health': 200,
        'damage': 15,
        'name': 'Demon',
        'attack_range': 1,
        'description': 'Tough opponent',
        'abilities': [('Fireball', {'ability_range': 3, 'power': 15, 'aoe': 0.75, 'need_los': True, 'cooldown': 300, }),
                      ('Call Imp', {'ability_range': 1, 'cooldown': 600, })],
    },
    'Imp': {
        'is_ranged': True,
        'portrait': 'portraits/Imp.png',
        'image_name': 'tiles/Imp.png',
        'health': 40,
        'damage': 8,
        'name': 'Imp',
        'attack_range': 2,
        'description': 'Small caster demon',
        'abilities': [('Lightning', {'ability_range': 5, 'damagefactor': 1})],
    },
    'Banshee': {
        'portrait': 'portraits/Necromancer.png',
        'image_name': 'tiles/Banshee.png',
        'health': 70,
        'damage': 5,
        'name': 'Banshee',
        'attack_range': 1,
        'abilities': [('Scream', {'power': 14, 'ability_range': 2, 'cooldown': 300, 'duration': 300})],
    },
}
