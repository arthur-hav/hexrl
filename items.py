from display import SimpleSprite

class Item(SimpleSprite):
    def __init__(self, image_name, stats_impact):
        super().__init__(image_name)
        self.stats_impact = stats_impact
        self.equipped_to = None

    def equip(self, creature):
        if self.equipped_to:
            self.unequip()
        creature.items.append(self)
        for k, v in self.stats_impact.items():
            setattr(creature, k, getattr(creature, k) + v)
        self.equipped_to = creature

    def unequip(self):
        self.equipped_to.items.remove(self)
        for k, v in self.stats_impact.items():
            setattr(self.equipped_to, k, getattr(self.equipped_to, k) - v)
        self.equipped_to = None

ITEMS = {
    'amulet_of_health':
        Item('tiles/AmuletOfHealth.png', {'health':20, 'maxhealth': 20})
        }
