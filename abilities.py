from display import SimpleSprite

class Ability(SimpleSprite):
    def __init__(self, name, image_name, **kwargs):
        super().__init__(image_name)
        self.name = name
        self.need_los = False
        self.image_name = image_name
        self.image_cd = image_name
        self.cooldown = 0
        self.ability_range = 0
        self.aoe = 0
        self.power = 0
        for k, v in kwargs.items():
            setattr(self, k, v)

    def range_hint(self, creature, target):
        if self.need_los:
            for tile in creature.tile.raycast(target):
                if tile != target and tile in creature.game.creatures and creature.game.creatures[tile].is_pc != creature.is_pc:
                    return False
        return creature.tile.dist(target) <= self.ability_range + 0.25

    def splash_hint(self, creature, selected, target):
        return False

class BoltAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target in creature.game.creatures \
                and creature.game.creatures[target].is_pc != creature.is_pc
    def apply_ability(self, creature, target):
        damage = self.power + round(creature.damage * self.damagefactor)
        for tile in creature.tile.raycast(target, go_through=True):
            if tile.dist(creature.tile) > self.ability_range:
                break
            target_cr = creature.game.creatures.get(tile, None)
            if target_cr and target_cr.is_pc != creature.is_pc:
                target_cr.take_damage(damage)
                creature.game.dmg_log_display.push_line(creature.image_name, self.image_name, damage)

    def splash_hint(self, creature, selected, target):
        return target in creature.tile.raycast(selected, go_through=True) and self.range_hint(creature, target)

class DamageAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target in creature.game.creatures \
                and creature.game.creatures[target].is_pc != creature.is_pc

    def apply_ability(self, creature, target):
        target_cr = creature.game.creatures[target]
        damage = self.power + round(creature.damage * self.damagefactor)
        target_cr.take_damage(damage)
        creature.game.dmg_log_display.push_line(creature.image_name, self.image_name, damage)

class AoeAbility(DamageAbility):
    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        target_cr = creature.game.creatures[target]
        damage = self.power + round(creature.damage * self.damagefactor * self.aoe)
        for tile in target_cr.tile.neighbours():
            splash_cr = creature.game.creatures.get(tile, None)
            if splash_cr and splash_cr.is_pc != creature.is_pc:
                splash_cr.take_damage(damage)
                creature.game.dmg_log_display.push_line(creature.image_name, self.image_name, damage)

    def splash_hint(self, creature, selected, target):
        return target in selected.neighbours()

class ShieldAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target in creature.game.creatures \
                and creature.game.creatures[target].is_pc == creature.is_pc
    def apply_ability(self, creature, target):
        power = self.power + round(creature.damage * self.damagefactor)
        target_cr = creature.game.creatures[target]
        target_cr.shield = max(target_cr.shield, power)
        creature.game.log_display.push_text("%s gains a magical shield." % (target_cr.name))

class NovaAbility(Ability):
    def is_valid_target(self, creature, target):
        return target == creature.tile

    def apply_ability(self, creature, target):
        damage = round(creature.damage * self.damagefactor)
        for cr in list(creature.game.creatures.values()):
            if creature.tile.dist(cr.tile) < self.ability_range and creature.is_pc != cr.is_pc:
                cr.take_damage(damage)
                creature.game.dmg_log_display.push_line(creature.image_name, self.image_name, damage)

    def splash_hint(self, creature, selected, target):
        return self.range_hint(creature, target)

class Invocation(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) and target not in creature.game.creatures

    def apply_ability(self, creature, target):
        from creatures import Creature
        c = Creature(self.defkey)
        c.set_in_game(creature.game, target, creature.next_action + 100)
        c.is_pc = creature.is_pc
        c.display()
        creature.game.log_display.push_text("%s raises %s !" % (creature.name, c.name))
