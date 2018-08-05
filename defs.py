class RangedDamageAbility():
    def __init__(self, ability_range, damage):
        self.ability_range = ability_range
        self.damage = damage

    def is_valid_target(self, creature, target):
        return (creature.tile.dist(target) <= self.ability_range \
                and target in creature.game.creatures)

    def apply_ability(self, creature, target):
        target_cr = creature.game.creatures[target]
        target_cr.take_damage(self.damage) 
        creature.game.log_display.push_text("%s hits %s for %d damage." % (creature.name, target_cr.name, self.damage))

PC1 = {
    'portrait': 'P1.png',
    'image_name': 'Fighter.png',
    'health': 100,
    'damage': 15,
    'speed': 10,
    'name': 'Fighter',
    'abilities': [],
    'is_pc': True
}
PC2 = {
    'portrait': 'P3.png',
    'image_name': 'Barbarian.png',
    'health': 80,
    'damage': 18,
    'speed': 10,
    'is_pc': True,
    'name': 'Barbarian',
    'abilities': []
}
PC3 = {
    'portrait': 'P1.png',
    'image_name': 'Archer.png',
    'health': 80,
    'damage': 10,
    'speed': 11,
    'name': 'Archer',
    'abilities': [{ 
        'name': 'arrow',
        'image_name': 'icons/arrow.png',
        'handler': RangedDamageAbility(5, 8)
    }],
    'is_pc': True
}



MOB1 = {
    'portrait': 'P2.png',
    'image_name': 'Gobelin.png',
    'health': 50,
    'damage': 8,
    'speed': 15,
    'name': 'Gobelin',
    'abilities': [],
    'is_pc': False
}
