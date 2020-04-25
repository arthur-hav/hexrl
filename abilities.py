from display import SimpleSprite
import random


class Ability(SimpleSprite):
    def __init__(self, name, image_name, **kwargs):
        super().__init__(image_name)
        self.name = name
        self.need_los = False
        self.is_instant = False
        self.image_name = image_name
        self.image_cd = image_name
        self.cooldown = 0
        self.current_cooldown = 0
        self.ability_range = 0
        self.aoe = 0
        self.power = 0
        self.health_cost = 0
        for k, v in kwargs.items():
            setattr(self, k, v)

    def range_hint(self, creature, target):
        if self.need_los:
            for tile in creature.tile.raycast(target):
                if tile != target and tile in creature.combat.creatures and creature.combat.creatures[tile].is_pc != creature.is_pc:
                    return False
        return creature.tile.dist(target) <= self.ability_range + 0.25

    def splash_hint(self, creature, selected, target):
        return False

    def apply_ability(self, creature, target):
        self.current_cooldown = self.cooldown

    def tick(self, creature, elapsed_time):
        self.current_cooldown = max(0, self.current_cooldown - elapsed_time)

    def get_ai_valid_target(self, creature):
        valid_targets = creature.combat.get_valid_targets(creature, self)
        if valid_targets:
            return random.choice(valid_targets)

class BoltAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target in creature.combat.creatures \
                and creature.combat.creatures[target].is_pc != creature.is_pc

    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        damage = self.power
        for tile in creature.tile.raycast(target, go_through=True):
            if tile.dist(creature.tile) > self.ability_range + 0.25:
                break
            target_cr = creature.combat.creatures.get(tile, None)
            if target_cr and target_cr.is_pc != creature.is_pc:
                target_cr.take_damage(damage, 'magic')
                # target_cr.game.dmg_log_display.push_line(creature.image_name, self.image_name, damage)

    def splash_hint(self, creature, selected, target):
        for tile in creature.tile.raycast(target, go_through=True):
            if tile.dist(creature.tile) > self.ability_range + 0.25:
                return False
            if tile == target:
                return True


class DamageAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target in creature.combat.creatures \
                and creature.combat.creatures[target].is_pc != creature.is_pc

    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        creature.health -= self.health_cost
        if creature.health <= 0:
            creature.health = 1
        target_cr = creature.combat.creatures[target]
        damage = self.power
        target_cr.take_damage(damage, self.damage_type)
        # creature.combat.dmg_log_display.push_line(creature.image_name, self.image_name, damage)


class AoeAbility(DamageAbility):
    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        damage = round(self.power * self.aoe)
        for tile in target.neighbours():
            splash_cr = creature.combat.creatures.get(tile, None)
            if splash_cr and splash_cr.is_pc != creature.is_pc:
                splash_cr.take_damage(damage)
                # creature.combat.dmg_log_display.push_line(creature.image_name, self.image_name, damage)

    def splash_hint(self, creature, selected, target):
        return target in selected.neighbours()


class ShieldAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target in creature.combat.creatures \
                and creature.combat.creatures[target].is_pc == creature.is_pc

    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        power = self.power  # + round(creature.damage * self.damagefactor)
        target_cr = creature.combat.creatures[target]
        target_cr.shield = max(target_cr.shield, power)
        # creature.combat.log_display.push_text("%s gains a magical shield." % (target_cr.name))


class NovaAbility(Ability):

    def is_valid_target(self, creature, target):
        return target == creature.tile

    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        damage = self.power
        for cr in list(creature.combat.creatures.values()):
            if creature.tile.dist(cr.tile) < self.ability_range + 0.25 and creature.is_pc != cr.is_pc:
                cr.take_damage(damage, self.damage_type)
                # creature.combat.dmg_log_display.push_line(creature.image_name, self.image_name, damage)

    def splash_hint(self, creature, selected, target):
        return self.range_hint(creature, target)

    def get_ai_valid_target(self, creature):
        for cr in list(creature.combat.creatures.values()):
            if creature.tile.dist(cr.tile) < self.ability_range + 0.25 and creature.is_pc != cr.is_pc:
                return creature.tile


class Invocation(Ability):

    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) and target not in creature.combat.creatures

    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        from creatures import Creature
        c = Creature(self.defkey)
        c.set_in_combat(creature.combat, target, creature.next_action + 100)
        c.is_pc = creature.is_pc
        # creature.combat.log_display.push_text("%s raises %s !" % (creature.name, c.name))


class StatusAbility(Ability):

    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) and target in creature.combat.creatures

    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        from status import STATUSES
        status_class = STATUSES[self.name][0]
        status_args = STATUSES[self.name][1]
        status_effect = status_class(self.duration, *status_args)
        target_cr = creature.combat.creatures[target]
        target_cr.add_status(status_effect)


class TeleportAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) and target not in creature.combat.creatures

    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        creature.combat.creatures[target] = creature
        del creature.combat.creatures[creature.tile]
        creature.tile = target
        creature.rect.x, creature.rect.y = creature.tile.display_location()


class EnnemyStatusAbility(StatusAbility):
    def is_valid_target(self, creature, target):
        return super().is_valid_target(creature, target) and creature.combat.creatures[target].is_pc != creature.is_pc


class ScreamAbility(Ability):
    def is_valid_target(self, creature, target):
        return self.range_hint(creature, target) \
                and target in creature.combat.creatures \
                and creature.combat.creatures[target].is_pc != creature.is_pc

    def apply_ability(self, creature, target):
        super().apply_ability(creature, target)
        damage = self.power
        from status import STATUSES
        status_class = STATUSES['Silence'][0]
        status_args = STATUSES['Silence'][1]
        status_effect = status_class(self.duration, *status_args)
        for cr in list(creature.combat.creatures.values()):
            if creature.tile.dist(cr.tile) < self.ability_range + 0.25 and creature.is_pc != cr.is_pc:
                cr.take_damage(damage, 'magic')
                # creature.combat.dmg_log_display.push_line(creature.image_name, self.image_name, damage)
                cr.add_status(status_effect)


ABILITIES = {
        'Raise Undead': (Invocation, {'name':'Raise undead', 'image_name':'icons/skull.png', 'image_cd':'icons/skull-cd.png',  'defkey':'Skeleton','description':'Places a skeleton on an empty tile of the battlefield.'}),
        'Call Imp': (Invocation, {'name':'Call Imp', 'image_name':'icons/skull.png', 'image_cd':'icons/skull-cd.png',  'defkey':'Imp', 'description':'Places an imp on an empty tile of the battlefield.'}),
        'Arrow': (DamageAbility, {'name' : 'Fire arrow', 'image_name' : 'icons/arrow.png',  'description' : 'Ranged attack for equal damage than melee', 'damage_type':'physical'}),
        'Smite': (DamageAbility, {'name' : 'Smite', 'image_name' : 'icons/smite.png', 'image_cd': 'icons/smite-cd.png',  'description' : 'Inflicts true damage in exchange for health', 'damage_type':'true'}),
        'Fireball': (AoeAbility, {'name' : 'Fireball', 'image_name' : 'icons/fireball.png', 'image_cd':'icons/fireball-cd.png', 'description' : 'Ranged attack inflicting splash damage on adjacent ennemies.', 'damage_type':'magic'}),
        'Lightning': (BoltAbility, {'name' : 'Lightning', 'image_name' : 'icons/lightning.png', 'image_cd':'icons/lightning-cd.png','description':'Ranged attack passing through a line of ennemies, damaging them.', 'damage_type':'magic'}),
        'Cleave': (NovaAbility, {'name' : 'Cleave', 'image_name':'icons/cleave.png', 'image_cd':'icons/cleave-cd.png', 'description': 'Simultaneously attack all ennemies in melee range', 'damage_type':'physical'}),
        'Shield': (ShieldAbility, {'name' : 'Shield', 'image_name':'icons/shield-icon.png', 'image_cd': 'icons/shield-icon-cd.png', 'description':'Shields an ally for a small amount of damage.'}),
        'Bloodlust': (StatusAbility, {'name':'Bloodlust', 'image_name':'icons/bloodlust.png', 'image_cd':'icons/bloodlust-cd.png', 'description':'Greatly enhances damage for a short period. Cast is instantaneous.'}),
        'Root': (EnnemyStatusAbility, {'name':'Root', 'image_name':'icons/root.png', 'image_cd':'icons/root-cd.png', 'description':'Target is made unable to move for a duration, and takes damage over time.'}),
        'Blink': (TeleportAbility, {'name':'Blink', 'image_name':'icons/blink.png', 'image_cd':'icons/blink-cd.png', 'description':'Transport yourself a short distance'}),
        'Scream': (ScreamAbility, {'name':'Scream', 'image_name':'icons/skull.png', 'image_cd':'icons/skull-cd.png', 'description':'Damages and silences nearby ennemies, making them unable to use abilities'})
}
