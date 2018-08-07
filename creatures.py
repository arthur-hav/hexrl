from display import SimpleSprite, CascadeElement, Gauge
import os
import random
import math


class SideHealthGauge(Gauge):
    def __init__(self, creature):
        self.creature = creature
        self.displayed = False
        super().__init__(4, 32, '#BB0008')
    def update(self):
        self.height = math.ceil((16 * self.creature.health) // self.creature.maxhealth) * 2
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
    def __init__ (self, defkey):
        for k, v in DEFS[defkey].items():
            setattr(self, k, v)
        self.defkey = defkey
        self.health_gauge = SideHealthGauge(self)
        self.shield_gauge = SideShieldGauge(self)
        self.maxhealth = self.health
        self.frames = []
        SimpleSprite.__init__(self, DEFS[defkey]['image_name']) 
        self.subsprites = [self.health_gauge, self.shield_gauge]
        self.ability_cooldown = [0 for _ in self.abilities]

    def set_in_game(self, game, game_tile, next_action):
        self.tile = game_tile
        self.rect.x, self.rect.y = self.tile.display_location()
        self.game = game
        self.game.creatures[game_tile] = self
        self.next_action = next_action
        self.shield = 0

    def update(self):
        if self.frames:
            self.animate(self.frames.pop(0))
        self.health_gauge.update()
        self.shield_gauge.update()
    
    def tick(self, elapsed_time):
        for i, v in enumerate(self.ability_cooldown):
            self.ability_cooldown[i] = max(0, v - elapsed_time)

    ### Below this : only valid if previously set_in_game

    def step_to(self, target):
        return min(self.tile.neighbours(), key = lambda x: x.dist(target))

    def move_or_attack(self, destination):
        if not destination.in_boundaries():
            return
        if destination in self.game.creatures and self.is_pc != self.game.creatures[destination].is_pc:
            return self.attack(destination)
        elif destination in self.game.creatures:
            #Swap places
            del self.game.creatures[self.tile]
            self.game.creatures[destination].move_or_attack(self.tile)
        else:
            del self.game.creatures[self.tile]
        self.tile = destination
        self.rect.x, self.rect.y = self.tile.display_location()
        self.game.creatures[destination] = self
        self.next_action += 1000 / self.speed
        if self.is_pc:
            self.game.new_turn()

    def attack(self, destination):
        creature = self.game.creatures[destination]
        creature.take_damage(self.damage)
        self.game.log_display.push_text("%s hits %s for %d damage." % (self.name, creature.name, self.damage))
        self.next_action += 100
        if self.is_pc:
            self.game.new_turn()

    def use_ability(self, ability, target):
        ability.apply_ability(self, target)
        self.next_action += 100
        if ability.cooldown:
            self.ability_cooldown[ self.abilities.index(ability) ] = ability.cooldown
        if self.is_pc:
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
            self.game.log_display.push_text("%s dies." % (self.name))
            del self.game.creatures[self.tile]
            self.erase()

    def get_valid_targets(self, creature, ability):
        valid_targets = [tile for tile in self.game.arena.board.keys() if ability.is_valid_target(self, tile)]
        return valid_targets

    def ai_play(self):
        nearest_pc = min( [c for c in self.game.creatures.values() if c.is_pc], 
                key= lambda x: x.tile.dist(self.tile))
        if self.abilities:
            ability_num = random.randint(0, len(self.abilities) - 1)
        if self.abilities and self.ability_cooldown[ability_num] == 0:
            valid_targets = self.get_valid_targets(self, self.abilities[ability_num])
            target = random.choice(valid_targets)
            self.use_ability(self.abilities[ability_num], target)
        else:
            self.move_or_attack(self.step_to(nearest_pc.tile))

    def display(self):
        CascadeElement.display(self)
        SimpleSprite.display(self)

    def erase(self):
        CascadeElement.erase(self)
        SimpleSprite.erase(self)

    def dict_dump(self):
        return {
            'health':self.health, 
            'defkey':self.defkey
            }
    @staticmethod 
    def dict_load(data):
        c = Creature(data['defkey'])
        c.health = data['health']
        return c

class Ability(SimpleSprite):
    def __init__(self, name, image_name, **kwargs):
        super().__init__(image_name)
        self.name = name
        self.need_los = False
        self.image_name = image_name
        self.image_cd = image_name
        self.cooldown = 0
        self.ability_range = 0
        for k, v in kwargs.items():
            setattr(self, k, v)

    def range_hint(self, creature, target):
        if self.need_los:
            for tile in creature.tile.raycast(target):
                if tile in creature.game.creatures and tile != target:
                    return False
        return creature.tile.dist(target) <= self.ability_range + 0.25


class DamageAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target in creature.game.creatures \
                and creature.game.creatures[target].is_pc != creature.is_pc

    def apply_ability(self, creature, target):
        target_cr = creature.game.creatures[target]
        target_cr.take_damage(self.damage) 
        creature.game.log_display.push_text("%s hits %s for %d damage." % (creature.name, target_cr.name, self.damage))

class ShieldAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target in creature.game.creatures \
                and creature.game.creatures[target].is_pc == creature.is_pc
    def apply_ability(self, creature, target):
        target_cr = creature.game.creatures[target]
        target_cr.shield = max(target_cr.shield, self.power)
        creature.game.log_display.push_text("%s gains a magical shield." % (target_cr.name))

class NovaAbility(Ability):
    def is_valid_target(self, creature, target):
        return target == creature.tile

    def apply_ability(self, creature, target):
        for cr in list(creature.game.creatures.values()):
            if creature.tile.dist(cr.tile) < self.ability_range and creature.is_pc != cr.is_pc:
                cr.take_damage(self.damage)
                creature.game.log_display.push_text("%s hits %s for %d damage." % (creature.name, cr.name, self.damage))

class Invocation(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target not in creature.game.creatures

    def apply_ability(self, creature, target):
        c = Creature(self.defkey)
        c.set_in_game(creature.game, target, creature.next_action + 100)
        c.is_pc = creature.is_pc
        c.display()
        creature.game.log_display.push_text("%s raises %s !" % (creature.name, c.name))

DEFS = {
    'Fighter': {
        'portrait': 'Fighter.png',
        'image_name': 'tiles/Fighter.png',
        'health': 100,
        'damage': 15,
        'speed': 10,
        'name': 'Fighter',
        'abilities': [ShieldAbility(name = 'Shield', image_name='icons/shield-icon.png', image_cd='icons/shield-icon-cd.png', ability_range=1, power=20, cooldown=300)],
        'is_pc': True
    },
    'Barbarian': {
        'portrait': 'Barbarian.png',
        'image_name': 'tiles/Barbarian.png',
        'health': 80,
        'damage': 18,
        'speed': 10,
        'is_pc': True,
        'name': 'Barbarian',
        'abilities': [NovaAbility(name = 'Cleave', image_name='icons/cleave.png', ability_range=1.01, damage=14)]
    },
    'Archer': {
        'portrait': 'Archer.png',
        'image_name': 'tiles/Archer.png',
        'health': 80,
        'damage': 10,
        'speed': 11,
        'name': 'Archer',
        'abilities': [ DamageAbility(name = 'Fire arrow', image_name = 'icons/arrow.png', ability_range = 5, damage = 10, need_los = True) ],
        'is_pc': True
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
        'is_pc': False
    },
    'Skeleton': {
        'portrait': 'Skeleton.png',
        'image_name': 'tiles/Skeleton.png',
        'description': 'Dangerous in great numbers.',
        'health': 65,
        'damage': 7,
        'speed': 7,
        'name': 'Skeleton',
        'abilities': [],
        'is_pc': False
    },
    'Necromancer': {
        'portrait': 'Necromancer.png',
        'image_name': 'tiles/Necromancer.png',
        'health': 70,
        'damage': 8,
        'speed': 8,
        'name': 'Necromancer',
        'description': 'Can raise undead',
        'abilities': [ Invocation(name='Raise undead', image_name='icons/skull.png', image_cd='icons/skull-cd.png',  defkey='Skeleton', ability_range=3, cooldown=300) ],
        'is_pc': False
    }
}
