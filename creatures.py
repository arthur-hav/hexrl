from display import SimpleSprite, CascadeElement, Gauge
from abilities import ABILITIES
from passives import PASSIVES
import os
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
        self.is_ranged = False
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
        self.game = None
        self.next_action = 0
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

    def set_in_game(self, game, game_tile, next_action):
        self.tile = game_tile
        self.rect.x, self.rect.y = self.tile.display_location()
        self.game = game
        self.game.creatures[game_tile] = self
        self.next_action = next_action
        self.shield = 0
        self.status = []

    def end_game(self):
        self.game = None
        self.tile = None

    def update(self):
        if self.frames:
            self.animate(self.frames.pop(0))
        self.health_gauge.update()
        self.shield_gauge.update()

    def dict_dump(self):
        items = self.items.copy()
        # This is so we dont stack stats by saving/loading with, say, a health amulet
        for item in self.items:
            item.unequip()
        d = {
            'items': [item.name for item in items],
            'health':self.health, 
            'defkey':self.defkey
            }
        for item in items:
            item.equip(self)
        return d

    @staticmethod 
    def dict_load(data, items):
        c = Creature(data['defkey'])
        c.health = data['health']
        for key in data['items']:
            for item in items:
                if item.name == key and not item.equipped_to:
                    item.equip(c)
                    break
        c.is_pc = True
        return c
    
    # Below this : only valid if previously set_in_game

    def tick(self, elapsed_time):
        for ability in self.abilities:
            ability.tick(self, elapsed_time)
        for status in self.status.copy():
            status.tick(self, elapsed_time)

    def step_to(self, target):
        return min(self.tile.neighbours(), key = lambda x: x.dist(target))

    def step_away(self, target):
        try:
            return max([t for t in self.tile.neighbours() if t not in self.game.creatures], key = lambda x: x.dist(target))
        except ValueError:
            return None

    def move_or_attack(self, destination):
        if not destination.in_boundaries():
            return
        if destination in self.game.creatures and self.is_pc != self.game.creatures[destination].is_pc:
            return self.attack(destination)
        elif self.rooted:
            return
        elif destination in self.game.creatures:
            # Swap places
            other_cr = self.game.creatures[destination]
            other_cr.tile = self.tile
            other_cr.rect.x, other_cr.rect.y = other_cr.tile.display_location()
            other_cr.game.creatures[self.tile] = other_cr
            del self.game.creatures[destination]
        else:
            del self.game.creatures[self.tile]
        self.tile = destination
        self.rect.x, self.rect.y = self.tile.display_location()
        self.game.creatures[destination] = self
        self.end_act()

    def idle(self):
        self.end_act()

    def end_act(self):
        self.next_action += 100

    def attack(self, destination):
        creature = self.game.creatures[destination]
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
            del self.game.creatures[self.tile]
            self.must_show = False

    def ai_play(self):
        nearest_pc = min([c for c in self.game.creatures.values() if c.is_pc],
                         key=lambda x: x.tile.dist(self.tile))
        # FLEEING
        if self.is_ranged and self.tile.dist(nearest_pc.tile) < 1.25:
            tile = self.step_away(nearest_pc.tile)
            if tile and tile.in_boundaries() and not self.rooted:
                self.move_or_attack(tile)
                return
        # CASTING
        if self.abilities and not self.silenced:
            ability = random.choice(self.abilities)
            if ability.current_cooldown == 0:
                valid_targets = self.game.get_valid_targets(self, ability)
                if valid_targets:
                    target = random.choice(valid_targets)
                    self.use_ability(ability, target)
                    return
        # HUNTING
        if not self.rooted or nearest_pc.tile.dist(self.tile) < 1.25:
            tile = self.step_to(nearest_pc.tile)
            # Only swap position with a lesser hp ally to avoid dancing
            if tile not in self.game.creatures or self.game.creatures[tile].is_pc != self.is_pc or self.game.creatures[tile].health < self.health:
                self.move_or_attack(tile)
                return
        # IDLE
        self.idle()

    def display(self):
        CascadeElement.display(self)
        SimpleSprite.display(self)


DEFS = {
    'Fighter': {
        'portrait': 'portraits/Fighter.png',
        'image_name': 'tiles/Fighter.png',
        'health': 100,
        'damage': 14,
        'armor':2,
        'magic_resist': 1,
        'name': 'Fighter',
        'abilities': [
            ('Smite', {'ability_range':2, 'power':4, 'damagefactor':1, 'health_cost':2, 'cooldown':300, 'need_los':False,}),
        ],
        'passives': [
            ('Shield', {'shield':5}),
        ]
    },
    'Barbarian': {
        'portrait': 'portraits/Barbarian.png',
        'image_name': 'tiles/Barbarian.png',
        'health': 90,
        'damage': 16,
        'armor':1,
        'magic_resist': 1,
        'name': 'Barbarian',
        'passives':[('Regeneration', {'rate': 2, 'maxhealth':25})],
        'abilities': [('Cleave', {'ability_range':1, 'damagefactor':1.2, 'cooldown':200})]
    },
    'Archer': {
        'portrait': 'portraits/Archer.png',
        'image_name': 'tiles/Archer.png',
        'health': 80,
        'damage': 12,
        'name': 'Archer',
        'abilities': [('Arrow', {'ability_range' : 4, 'damagefactor':1, 'need_los' : True,})],
    },
    'Wizard': {
        'portrait': 'portraits/Wizard.png',
        'image_name': 'tiles/Wizard.png',
        'health': 70,
        'damage': 10,
        'name': 'Wizard',
        'passives':[('Fastcast', {'cdr':3})],
        'abilities': [('Fireball', {'ability_range' : 3, 'power':5, 'damagefactor':1, 'aoe':0.75, 'need_los' : True, 'cooldown':200,})],
    },
    'Enchantress': {
        'portrait': 'portraits/Elf.png',
        'image_name': 'tiles/Elf.png',
        'health': 70,
        'damage': 10,
        'name': 'Enchantress',
        'abilities': [('Root', {'ability_range':5, 'cooldown':0, 'duration':200})],
    },


    'Gobelin': {
        'portrait': 'portraits/Gobelin.png',
        'image_name': 'tiles/Gobelin.png',
        'health': 50,
        'damage': 8,
        'name': 'Gobelin',
        'abilities': [],
    },
    'Troll': {
        'portrait': 'portraits/Gobelin.png',
        'image_name': 'tiles/Troll.png',
        'health': 70,
        'armor':3,
        'damage': 12,
        'name': 'Troll',
        'abilities': [],
        'passives':[('Regeneration', {'rate': 6, 'maxhealth':None})]
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
        'is_ranged': True,
        'portrait': 'portraits/Skeleton.png',
        'image_name': 'tiles/SkeletonArcher.png',
        'description': 'Ranged',
        'health': 50,
        'damage': 5,
        'name': 'Skeleton Archer',
        'abilities': [('Arrow', {'ability_range': 3, 'damagefactor':1, 'need_los' : True,})],
    },
    'Necromancer': {
        'is_ranged': True,
        'portrait': 'portraits/Necromancer.png',
        'image_name': 'tiles/Necromancer.png',
        'health': 70,
        'damage': 7,
        'name': 'Necromancer',
        'description': 'Can raise undead',
        'abilities': [('Raise Undead', {'ability_range':2, 'cooldown':300,})],
    },
    'Demon': {
        'is_ranged': False,
        'portrait': 'portraits/Demon.png',
        'image_name': 'tiles/Demon.png',
        'health': 200,
        'damage': 15,
        'name': 'Demon',
        'description': 'Tough opponent',
        'abilities': [('Fireball', {'ability_range' : 3, 'damagefactor':1, 'aoe':0.75, 'need_los' : True, 'cooldown':300,}),
            ('Call Imp', {'ability_range':1, 'cooldown':600,}) ],
    },
    'Imp': {
        'is_ranged': True,
        'portrait': 'portraits/Imp.png',
        'image_name': 'tiles/Imp.png',
        'health': 40,
        'damage': 8,
        'name': 'Imp',
        'description': 'Small caster demon',
        'abilities': [('Lightning', {'ability_range' : 5, 'power':4, 'damagefactor':1, 'cooldown':200,})],
    },
    'Banshee': {
        'portrait': 'portraits/Necromancer.png',
        'image_name': 'tiles/banshee.png',
        'health': 80,
        'damage': 10,
        'name': 'Banshee',
        'abilities': [('Scream', {'ability_range': 2, 'damagefactor': 1, 'cooldown': 200, 'duration':300 })],
    },
}
