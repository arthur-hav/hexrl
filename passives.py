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

        old_end_game = creature.end_game

        def new_end_game():
            old_end_game()
            creature.health = max(creature.health, self.maxhealth or creature.maxhealth)
        creature.end_game = new_end_game

    def get_short_desc(self):
        t = 'Regen +%d' % self.rate
        if self.maxhealth:
            t += ' to %d' % self.maxhealth
        return t

    def get_description(self):
        t = 'Regenerates %d health per turn' % self.rate
        if self.maxhealth:
            t += ' when below %d health' % self.maxhealth
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
            i = creature.abilities.index(ability) 
            val = creature.ability_cooldown[i]
            creature.ability_cooldown[i] = round(10 * val / (self.cdr + 10))
        creature.use_ability = use_ability

    def get_short_desc(self):
        return 'Fastcast %s' % self.cdr

    def get_description(self):
        return 'Divides all cooldown by %.1f' % (1 + self.cdr / 10)


PASSIVES = {
        'Regeneration': (RegenerationPassive, {'name': 'Regeneration', 'image_name':'icons/heart.png'}),
        'Shield': (ShieldPassive, {'name': 'Shield', 'image_name':'icons/shield-icon.png'}),
        'Fastcast': (CooldownReduction, {'name': 'Fastcast', 'image_name':'icons/smite.png'}),
}
