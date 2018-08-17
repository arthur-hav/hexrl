class Passive():
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
            creature.health += round(elapsed_time / 100 * self.rate)
            creature.health = min(creature.health, creature.maxhealth)
        creature.tick = new_tick
    def get_short_desc(self):
        return 'Regeneration %d' % self.rate
    def get_description(self):
        return 'Regenerates %d health per turn' % self.rate

class ShieldPassive(Passive):
    def apply_to(self, creature):
        def act():
            creature.next_action += 100
            creature.shield = max(creature.shield, self.shield)
        creature.act = act
    def get_short_desc(self):
        return 'Shield %d' % self.shield
    def get_description(self):
        return 'Every turn, gains a shield preventing %d damage' % self.shield


PASSIVES = {
        'Regeneration': (RegenerationPassive, {'name': 'Regeneration', 'image_name':'icons/heart.png'}),
        'Shield': (ShieldPassive, {'name': 'Shield', 'image_name':'icons/shield-icon.png'}),
}
