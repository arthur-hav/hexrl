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

DEFS = {
    'Fighter': {
        'portrait': 'P1.png',
        'image_name': 'Fighter.png',
        'health': 100,
        'damage': 15,
        'speed': 10,
        'name': 'Fighter',
        'abilities': [],
        'is_pc': True
    },
    'Barbarian': {
        'portrait': 'P3.png',
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
        'portrait': 'P1.png',
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
        'portrait': 'P2.png',
        'image_name': 'Gobelin.png',
        'health': 50,
        'damage': 8,
        'speed': 15,
        'name': 'Gobelin',
        'abilities': [],
        'is_pc': False
    }
}
