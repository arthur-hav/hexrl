from display import SimpleSprite, CascadeElement, Gauge
from abilities import BoltAbility, DamageAbility, AoeAbility, NovaAbility, Invocation, ShieldAbility, ABILITIES
import os
import random
import math


class SideHealthGauge(Gauge):
    def __init__(self, creature):
        self.creature = creature
        self.displayed = False
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
        self.displayed = False
        super().__init__(4, 32, '#BBCCFF')
    def update(self):
        self.height = math.ceil((16 * self.creature.shield) // self.creature.maxhealth) * 2
        self.rect.x, self.rect.y = self.creature.tile.display_location()
        self.rect.y += 32 - self.height
        self.set_height(self.height)

class Creature(SimpleSprite, CascadeElement):
    def __init__ (self, defkey, is_pc=False):
        self.is_ranged = False
        for k, v in DEFS[defkey].items():
            setattr(self, k, v)
        self.abilities = [ABILITIES[k] for k in self.abilities]
        self.is_pc = is_pc
        self.defkey = defkey
        self.health_gauge = SideHealthGauge(self)
        self.shield_gauge = SideShieldGauge(self)
        self.maxhealth = self.health
        self.frames = []
        SimpleSprite.__init__(self, DEFS[defkey]['image_name']) 
        self.subsprites = [self.health_gauge, self.shield_gauge]
        self.items = []

    def set_in_game(self, game, game_tile, next_action):
        self.tile = game_tile
        self.rect.x, self.rect.y = self.tile.display_location()
        self.game = game
        self.game.creatures[game_tile] = self
        self.next_action = next_action
        self.shield = 0
        self.ability_cooldown = [0, 0, 0]
        self.status_cooldown = []
        self.status = []

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
    
    ### Below this : only valid if previously set_in_game

    def tick(self, elapsed_time):
        for i, v in enumerate(self.ability_cooldown):
            self.ability_cooldown[i] = max(0, v - elapsed_time)
        for status in self.status:
            status.tick(self, elapsed_time)
        for i, v in enumerate(self.status_cooldown):
            self.status_cooldown[i] = max(0, v - elapsed_time)
            if self.status_cooldown[i] == 0:
                self.status[i].status_end(self)
                self.status.pop(i)
                self.status_cooldown.pop(i)

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
        elif self.speed <= 0:
            return
        elif destination in self.game.creatures:
            #Swap places
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
        self.next_action += 1000 // self.speed
        if self.is_pc:
            self.game.new_turn()

    def attack(self, destination):
        creature = self.game.creatures[destination]
        creature.take_damage(self.damage)
        self.game.dmg_log_display.push_line(self.image_name, 'icons/sword.png', self.damage)
        self.next_action += 100
        if self.is_pc:
            self.game.new_turn()

    def use_ability(self, ability, target):
        ability.apply_ability(self, target)
        if ability.cooldown:
            self.ability_cooldown[ self.abilities.index(ability) ] = ability.cooldown
        if not ability.is_instant:
            self.next_action += 100
            if self.is_pc and not ability.is_instant:
                self.game.new_turn()

    def take_damage(self, number):
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
            self.game.log_display.push_text("%s dies." % (self.name))
            del self.game.creatures[self.tile]
            self.erase()


    def ai_play(self):
        nearest_pc = min( [c for c in self.game.creatures.values() if c.is_pc], 
                key= lambda x: x.tile.dist(self.tile))
        #FLEEING
        if self.is_ranged and self.tile.dist(nearest_pc.tile) < 1.25:
            tile = self.step_away(nearest_pc.tile)
            if tile and tile.in_boundaries() and self.speed > 0:
                self.move_or_attack(tile)
                return
        #CASTING
        if self.abilities:
            ability_num = random.randint(0, len(self.abilities) - 1)
        valid_targets = None
        if self.abilities and self.ability_cooldown[ability_num] == 0:
            valid_targets = self.game.get_valid_targets(self, self.abilities[ability_num])
        if valid_targets:
            target = random.choice(valid_targets)
            self.use_ability(self.abilities[ability_num], target)
            return
        #HUNTING
        if self.speed > 0 or nearest_pc.tile.dist(self.tile) < 1.25:
            self.move_or_attack(self.step_to(nearest_pc.tile))
            return
        self.next_action += 50

    def display(self):
        CascadeElement.display(self)
        SimpleSprite.display(self)

    def erase(self):
        CascadeElement.erase(self)
        SimpleSprite.erase(self)



DEFS = {
    'Fighter': {
        'portrait': 'Fighter.png',
        'image_name': 'tiles/Fighter.png',
        'health': 100,
        'damage': 16,
        'speed': 10,
        'name': 'Fighter',
        'abilities': ['Shield'],
    },
    'Barbarian': {
        'portrait': 'Barbarian.png',
        'image_name': 'tiles/Barbarian.png',
        'health': 80,
        'damage': 16,
        'speed': 10,
        'is_pc': True,
        'name': 'Barbarian',
        'abilities': ['Cleave']
    },
    'Archer': {
        'portrait': 'Archer.png',
        'image_name': 'tiles/Archer.png',
        'health': 80,
        'damage': 12,
        'speed': 12,
        'name': 'Archer',
        'abilities': ['Long bow'],
    },
    'Wizard': {
        'portrait': 'Wizard.png',
        'image_name': 'tiles/Wizard.png',
        'health': 70,
        'damage': 10,
        'speed': 8,
        'name': 'Wizard',
        'abilities': ['Fireball', 'Lightning'],
    },
    'Enchantress': {
        'portrait': 'Elf.png',
        'image_name': 'tiles/Elf.png',
        'health': 70,
        'damage': 10,
        'speed': 10,
        'name': 'Enchantress',
        'abilities': ['Root'],
    },


    'Gobelin': {
        'portrait': 'Gobelin.png',
        'image_name': 'tiles/Gobelin.png',
        'description': 'Fast.',
        'health': 50,
        'damage': 8,
        'speed': 15,
        'name': 'Gobelin',
        'abilities': [],
    },
    'Skeleton': {
        'portrait': 'Skeleton.png',
        'image_name': 'tiles/Skeleton.png',
        'description': 'Dangerous in great numbers.',
        'health': 60,
        'damage': 7,
        'speed': 7,
        'name': 'Skeleton',
        'abilities': [],
    },
    'SkeletonArcher': {
        'is_ranged': True,
        'portrait': 'Skeleton.png',
        'image_name': 'tiles/SkeletonArcher.png',
        'description': 'Ranged',
        'health': 50,
        'damage': 5,
        'speed': 7,
        'name': 'Skeleton',
        'abilities': ['Short bow'],
    },
    'Necromancer': {
        'is_ranged': True,
        'portrait': 'Necromancer.png',
        'image_name': 'tiles/Necromancer.png',
        'health': 70,
        'damage': 7,
        'speed': 7,
        'name': 'Necromancer',
        'description': 'Can raise undead',
        'abilities': ['Raise Undead'],
    },
    'Demon': {
        'is_ranged': False,
        'portrait': 'Demon.png',
        'image_name': 'tiles/Demon.png',
        'health': 200,
        'damage': 15,
        'speed': 10,
        'name': 'Demon',
        'description': 'Very tough opponent',
        'abilities': ['Fireball'],
    }
}
