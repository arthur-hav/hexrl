from display import SimpleSprite

class Item(SimpleSprite):
    def __init__(self, key):
        self.key = key
        for k, v in ITEMS[key].items():
            setattr(self, k, v)
        self.equipped_to = None
        super().__init__(self.image_name)

    def stats_string(self):
        t = ['%s %+d' % (k, v) for k, v in ITEMS[self.key]['stat_impact'].items()]
        return ' '.join(t)

    def equip(self, creature):
        if self.equipped_to:
            self.unequip()
        creature.items.append(self)
        for k, v in self.stat_impact.items():
            setattr(creature, k, getattr(creature, k) + v)
        self.equipped_to = creature

    def unequip(self):
        self.equipped_to.items.remove(self)
        for k, v in self.stat_impact.items():
            setattr(self.equipped_to, k, getattr(self.equipped_to, k) - v)
        self.equipped_to = None

ITEMS = {
    'amulet_of_health':
    {
        'name': 'Amulet of Health',
        'image_name':'tiles/AmuletOfHealth.png',
        'stat_impact': { 
            'health':20, 
            'maxhealth': 20
        },
        'shop_price': 100
    },
    'amulet_of_speed':
    {
        'name': 'Amulet of Speed',
        'image_name':'tiles/AmuletOfSpeed.png',
        'stat_impact': { 
            'speed':2
        },
        'shop_price': 25
    },
    'amulet_of_damage':
    {
        'name': 'Amulet of the Berserk',
        'image_name':'tiles/AmuletRubis.png',
        'stat_impact': { 
            'damage':4,
            'speed':2,
            'health':-10,
            'maxhealth':-10
        },
        'shop_price': 200
    }
}
