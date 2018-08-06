from display import SimpleSprite, CascadeElement, Gauge
import os
import random

class SideHealthGauge(Gauge):
    def __init__(self, creature):
        self.creature = creature
        self.displayed = False
        super(SideHealthGauge, self).__init__(4, 32, '#BB0008')
    def update(self):
        self.height = (8 + 16 * self.creature.health) // self.creature.maxhealth * 2
        self.rect.x, self.rect.y = self.creature.tile.display_location()
        self.rect.y += 32 - self.height
        self.set_height(self.height)
        if self.creature.health == self.creature.maxhealth:
            self.set_height(0)

class Creature(SimpleSprite, CascadeElement):
    def __init__ (self, defkey):
        for k, v in DEFS[defkey].items():
            setattr(self, k, v)
        self.defkey = defkey
        self.gauge = SideHealthGauge(self)
        self.maxhealth = self.health
        self.frames = []
        SimpleSprite.__init__(self, os.path.join('tiles', DEFS[defkey]['image_name'])) 
        self.subsprites = [self.gauge]

    def set_in_game(self, game, game_tile, next_action):
        self.tile = game_tile
        self.rect.x, self.rect.y = self.tile.display_location()
        self.game = game
        self.game.creatures[game_tile] = self
        self.next_action = next_action

    def update(self):
        if self.frames:
            self.animate(self.frames.pop(0))
        self.gauge.update()

    ### Below this : only valid if previously set_in_game

    def step_to(self, target):
        return min(self.tile.neighbours(), key = lambda x: x.dist(target))

    def move_or_attack(self, destination):
        self.next_action += 1000 / self.speed
        if destination in self.game.creatures or not destination.in_boundaries():
            return self.attack(destination)
        del self.game.creatures[self.tile]
        self.tile = destination
        self.rect.x, self.rect.y = self.tile.display_location()
        self.game.creatures[destination] = self

    def attack(self, destination):
        creature = self.game.creatures[destination]
        creature.take_damage(self.damage)
        self.game.log_display.push_text("%s hits %s for %d damage." % (self.name, creature.name, self.damage))

    def take_damage(self, number):
        self.health -= number
        self.frames.extend(['tiles/Hit.png', 'tiles/' + self.image_name])
        if self.health < 0:
            self.game.log_display.push_text("%s dies." % (self.name))
            del self.game.creatures[self.tile]
            self.erase()

    def ai_play(self):
        nearest_pc = min( [c for c in self.game.creatures.values() if c.is_pc], 
                key= lambda x: x.tile.dist(self.tile))
        if self.abilities and random.random() > 0.6:
            ability = random.choice(self.abilities)['handler']
            valid_targets = self.game.get_valid_targets(self, ability)
            target = random.choice(valid_targets)
            time_spent = ability.apply_ability(self, target)
            self.next_action += time_spent / self.speed
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

class RangedDamageAbility():
    def __init__(self, ability_range, damage, need_los = True):
        self.ability_range = ability_range
        self.damage = damage
        self.need_los = need_los

    def is_valid_target(self, creature, target):
        if self.need_los:
            for tile in creature.tile.raycast(target):
                if tile in creature.game.creatures and tile != target:
                    return False
        return creature.tile.dist(target) <= self.ability_range \
                and target in creature.game.creatures \
                and creature.game.creatures[target].is_pc != creature.is_pc

    def apply_ability(self, creature, target):
        target_cr = creature.game.creatures[target]
        target_cr.take_damage(self.damage) 
        creature.game.log_display.push_text("%s hits %s for %d damage." % (creature.name, target_cr.name, self.damage))
        return 1000

class NovaAbility():
    def __init__(self, ability_range, damage, need_los = False):
        self.ability_range = ability_range
        self.damage = damage
        self.need_los = need_los

    def is_valid_target(self, creature, target):
        return target == creature.tile

    def apply_ability(self, creature, target):
        for cr in list(creature.game.creatures.values()):
            if creature.tile.dist(cr.tile) < self.ability_range and creature.is_pc != cr.is_pc:
                cr.take_damage(self.damage)
                creature.game.log_display.push_text("%s hits %s for %d damage." % (creature.name, cr.name, self.damage))
        return 1000

class Invocation():
    def __init__(self, defkey, ability_range = 3):
        self.ability_range = ability_range
        self.defkey = defkey
    def is_valid_target(self, creature, target):
        return creature.tile.dist(target) <= self.ability_range \
                and target not in creature.game.creatures
    def apply_ability(self, creature, target):
        c = Creature(self.defkey)
        c.set_in_game(creature.game, target, creature.next_action + 100)
        c.is_pc = creature.is_pc
        c.display()
        creature.game.log_display.push_text("%s raises %s !" % (creature.name, c.name))
        return 1000

DEFS = {
    'Fighter': {
        'portrait': 'Fighter.png',
        'image_name': 'Fighter.png',
        'health': 100,
        'damage': 15,
        'speed': 10,
        'name': 'Fighter',
        'abilities': [{ 
            'name': 'Raise undead',
            'image_name':'icons/skull.png',
            'handler': Invocation('Skeleton')
        }],
        'is_pc': True
    },
    'Barbarian': {
        'portrait': 'Barbarian.png',
        'image_name': 'Barbarian.png',
        'health': 80,
        'damage': 18,
        'speed': 10,
        'is_pc': True,
        'name': 'Barbarian',
        'abilities': [{
            'name': 'cleave',
            'image_name': 'icons/cleave.png',
            'handler': NovaAbility(1.1, 14)
        }]
    },
    'Archer': {
        'portrait': 'Archer.png',
        'image_name': 'Archer.png',
        'health': 80,
        'damage': 10,
        'speed': 11,
        'name': 'Archer',
        'abilities': [{ 
            'name': 'arrow',
            'image_name': 'icons/arrow.png',
            'handler': RangedDamageAbility(5, 10)
        }],
        'is_pc': True
    },
    'Gobelin': {
        'portrait': 'Gobelin.png',
        'image_name': 'Gobelin.png',
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
        'image_name': 'Skeleton.png',
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
        'image_name': 'Necromancer.png',
        'health': 70,
        'damage': 8,
        'speed': 8,
        'name': 'Necromancer',
        'description': 'Can raise undead',
        'abilities': [{ 
            'name': 'Raise undead',
            'image_name':'icons/skull.png',
            'handler': Invocation('Skeleton')
        }],
        'is_pc': False
    }
}
