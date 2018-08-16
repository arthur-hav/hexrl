from display import SimpleSprite

class Ability(SimpleSprite):
    def __init__(self, name, image_name, **kwargs):
        super().__init__(image_name)
        self.name = name
        self.need_los = False
        self.is_instant = False
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
            if tile.dist(creature.tile) > self.ability_range + 0.25:
                break
            target_cr = creature.game.creatures.get(tile, None)
            if target_cr and target_cr.is_pc != creature.is_pc:
                target_cr.take_damage(damage, 'magic')
                target_cr.game.dmg_log_display.push_line(creature.image_name, self.image_name, damage)

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
        target_cr.take_damage(damage, self.damage_type)
        creature.game.dmg_log_display.push_line(creature.image_name, self.image_name, damage)

class AoeAbility(DamageAbility):
    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        damage = self.power + round(creature.damage * self.damagefactor * self.aoe)
        for tile in target.neighbours():
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
        power = self.power #+ round(creature.damage * self.damagefactor)
        target_cr = creature.game.creatures[target]
        target_cr.shield = max(target_cr.shield, power)
        creature.game.log_display.push_text("%s gains a magical shield." % (target_cr.name))

class NovaAbility(Ability):
    def is_valid_target(self, creature, target):
        return target == creature.tile

    def apply_ability(self, creature, target):
        damage = round(creature.damage * self.damagefactor)
        for cr in list(creature.game.creatures.values()):
            if creature.tile.dist(cr.tile) < self.ability_range + 0.25 and creature.is_pc != cr.is_pc:
                cr.take_damage(damage, self.damage_type)
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
        c.game.subsprites.insert(7, c)
        creature.game.log_display.push_text("%s raises %s !" % (creature.name, c.name))

class StatusAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) and target in creature.game.creatures

    def apply_ability(self, creature, target):
        from status import STATUSES
        status_class = STATUSES[self.name][0]
        status_args = STATUSES[self.name][1]
        status_effect = status_class(*status_args)
        target_cr = creature.game.creatures[target]
        for i, status in enumerate(target_cr.status):
            if status_class == status.__class__:
                target_cr.status_cooldown[i] = max(target_cr.status_cooldown[i], self.duration)
                return
        target_cr.status.append(status_effect)
        target_cr.status_cooldown.append(self.duration)
        status_effect.status_start(target_cr)

class TeleportAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) and target not in creature.game.creatures

    def apply_ability(self, creature, target):
        creature.game.creatures[target] = creature
        del creature.game.creatures[creature.tile]
        creature.tile = target
        creature.rect.x, creature.rect.y = creature.tile.display_location()

class EnnemyStatusAbility(StatusAbility):
    def is_valid_target(self, creature, target):
        return super().is_valid_target(creature, target) and creature.game.creatures[target].is_pc != creature.is_pc


ABILITIES = {
        'Raise Undead': (Invocation, {'name':'Raise undead', 'image_name':'icons/skull.png', 'image_cd':'icons/skull-cd.png',  'defkey':'Skeleton','description':'Places a skeleton on an empty tile of the battlefield.'}),
        'Call Imp': (Invocation, {'name':'Call Imp', 'image_name':'icons/skull.png', 'image_cd':'icons/skull-cd.png',  'defkey':'Imp', 'description':'Places an imp on an empty tile of the battlefield.'}),
        'Arrow': (DamageAbility, {'name' : 'Fire arrow', 'image_name' : 'icons/arrow.png',  'description' : 'Ranged attack for equal damage than melee', 'damage_type':'physical'}),
        'Fireball': (AoeAbility, {'name' : 'Fireball', 'image_name' : 'icons/fireball.png', 'image_cd':'icons/fireball-cd.png', 'description' : 'Ranged attack inflicting splash damage on adjacent ennemies.', 'damage_type':'magic'}),
        'Lightning': (BoltAbility, {'name' : 'Lightning', 'image_name' : 'icons/lightning.png', 'image_cd':'icons/lightning-cd.png','description':'Ranged attack passing through a line of ennemies, damaging them.', 'damage_type':'magic'}),
        'Cleave': (NovaAbility, {'name' : 'Cleave', 'image_name':'icons/cleave.png',  'description':'Simultaneously attack all ennemies in melee range', 'damage_type':'physical'}),
        'Shield': (ShieldAbility, {'name' : 'Shield', 'image_name':'icons/shield-icon.png', 'image_cd':'icons/shield-icon-cd.png', 'description':'Shields an ally for a small amount of damage.'}),
        'Bloodlust': (StatusAbility, {'name':'Bloodlust', 'image_name':'icons/bloodlust.png', 'image_cd':'icons/bloodlust-cd.png', 'description':'Greatly enhances damage for a short period. Cast is instantaneous.'}),
        'Root': (EnnemyStatusAbility, {'name':'Root', 'image_name':'icons/root.png', 'image_cd':'icons/root-cd.png', 'description':'Target is made unable to move for a duration, and takes damage over time.'}),
        'Blink': (TeleportAbility, {'name':'Blink', 'image_name':'icons/blink.png', 'image_cd':'icons/blink-cd.png', 'description':'Transport yourself a short distance'}),
}
