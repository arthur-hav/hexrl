class Passive:
    def __init__(self, image_name, **kwargs):
        self.image_name = image_name
        for k, v in kwargs.items():
            setattr(self, k, v)
    def apply_to(self, creature):
        pass
    def get_short_desc(self):
        pass


class RegenerationPassive(Passive):
    def apply_to(self, creature):
        old_tick = creature.tick

        def new_tick(elapsed_time):
            old_tick(elapsed_time)
            if creature.health < (self.maxhealth or creature.maxhealth):
                creature.health += round(elapsed_time / 100 * self.rate)
        creature.tick = new_tick

        old_end_game = creature.end_combat

        def new_end_game():
            old_end_game()
            creature.health = max(creature.health, self.maxhealth or creature.maxhealth)
        creature.end_combat = new_end_game

    def get_short_desc(self):
        t = 'Regen %d' % self.rate
        if self.maxhealth:
            t += ' below %d' % self.maxhealth
        return t

    def get_description(self):
        t = 'Regenerates %d health per turn' % self.rate
        if self.maxhealth:
            t += ' when below %d health' % self.maxhealth
        return t


class HealPassive(Passive):
    def apply_to(self, creature):
        old_end_combat = creature.end_combat

        def new_end_combat():
            for cr in creature.combat.creatures.values():
                if cr.health > 0:
                    cr.health += self.amount
                    cr.health = min(cr.health, cr.maxhealth)
            old_end_combat()
        creature.end_combat = new_end_combat

    def get_short_desc(self):
        t = 'Heal %d' % self.amount
        return t

    def get_description(self):
        t = 'Heals all party for %d health after every combat' % self.amount
        return t


class ShieldPassive(Passive):
    def apply_to(self, creature):
        old_end_act = creature.end_act

        def end_act():
            old_end_act()
            creature.shield = max(creature.shield, self.shield)
        creature.end_act = end_act

    def get_short_desc(self):
        return 'Shield %d' % self.shield

    def get_description(self):
        return 'Every turn, gains a shield preventing %d damage' % self.shield


class CooldownReduction(Passive):
    def apply_to(self, creature):
        old_use = creature.use_ability

        def use_ability(ability, target):
            old_use(ability, target)
            ability.current_cooldown = round(10 * ability.current_cooldown / (self.cdr + 10))
        creature.use_ability = use_ability

    def get_short_desc(self):
        return 'Fastcast %s' % self.cdr

    def get_description(self):
        return 'Divides all cooldown by %.1f' % (1 + self.cdr / 10)


PASSIVES = {
        'Regeneration': (RegenerationPassive, {'name': 'Regeneration', 'image_name':'icons/heartplus.png'}),
        'Shield': (ShieldPassive, {'name': 'Shield', 'image_name':'icons/shield-icon.png'}),
        'Fastcast': (CooldownReduction, {'name': 'Fastcast', 'image_name':'icons/smite.png'}),
        'PartyHeal': (HealPassive, {'name': 'PartyHeal', 'image_name':'icons/heart.png'}),
}
