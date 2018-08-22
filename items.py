from display import SimpleSprite
from abilities import ABILITIES


class Item(SimpleSprite):
    def __init__ (self, name, image_name, shop_price):
        super().__init__(image_name)
        self.name = name
        self.image_name = image_name
        self.shop_price = shop_price
        self.equipped_to = None
        self.consumable = False

    def equip(self, creature):
        equipped_to = self.equipped_to
        if equipped_to != creature:
            creature.items.append(self)
            self.equipped_to = creature
            self.on_equip(creature)

    def unequip(self):
        self.on_unequip()
        self.equipped_to.items.remove(self)
        self.equipped_to = None


class Consumable(SimpleSprite):
    def __init__(self, name, image_name, shop_price):
        super().__init__(image_name)
        self.name = name
        self.image_name = image_name
        self.shop_price = shop_price
        self.consumable = True
        self.equipped_to = None


class StatsItem(Item):
    def __init__(self, name, image_name, shop_price, stat_impact):
        super().__init__(name, image_name, shop_price)
        self.stat_impact = stat_impact
    def __str__(self):
        t = ['%s %+d' % (k, v) for k, v in self.stat_impact.items() if k != 'health']
        return 'This item gives ' + ' '.join(t)

    def on_equip(self, creature):
        for k, v in self.stat_impact.items():
            setattr(self.equipped_to, k, getattr(self.equipped_to, k) + v)

    def on_unequip(self):
        for k, v in self.stat_impact.items():
            setattr(self.equipped_to, k, getattr(self.equipped_to, k) - v)


class AbilityItem(Item):
    def __init__(self, name, image_name, shop_price, ability, ability_def):
        super().__init__(name, image_name, shop_price)
        self.ability = ABILITIES[ability]
        self.ability_def = self.ability[1].copy()
        self.ability_def.update(ability_def)
        self.ability = self.ability[0](**self.ability_def)

    def __str__(self):
        return 'This item gives the ability %s' % self.ability_def['name']

    def on_equip(self, creature):
        creature.abilities.append(self.ability)
    def on_unequip(self):
        self.equipped_to.abilities.remove(self.ability)


class HealthPotion(Consumable):
    def __str__(self):
        return 'This item gives back full health on use'

    def equip(self, creature):
        creature.health = creature.maxhealth


class DamageElixir(Consumable):
    def __str__(self):
        return 'This item permanently increases damage'

    def equip(self, creature):
        creature.damage += 1


class HealthElixir(Consumable):
    def __str__(self):
        return 'This item permanently increases max health'

    def equip(self, creature):
        creature.maxhealth += 10
        creature.health += 10


ITEMS = {
    'Life pendant': (StatsItem, ('Life pendant', 'tiles/AmuletOfHealth.png', 100, { 'health': 20, 'maxhealth': 20 })),
    'Lightfoot amulet': (AbilityItem, ('Lightfoot amulet','tiles/AmuletOfSpeed.png', 50, 'Blink',{'ability_range':2, 'cooldown': 200} )),
    'Bloodluster': (AbilityItem, ('Bloodluster','tiles/AmuletRubis.png', 200, 'Bloodlust', {'ability_range':0, 'cooldown':700, 'duration': 250, 'is_instant': True,})),
    'Protector': (AbilityItem, ('Protector', 'tiles/AmuletSaphir.png', 200, 'Shield', {'ability_range': 2, 'cooldown': 400, 'power':20})),
    'Health potion': (HealthPotion, ('Health potion', 'tiles/red-potion.png', 15)),
    'Elixir of might': (DamageElixir, ('Elixir of might', 'tiles/blue-potion.png', 120)),
    'Elixir of endurance': (HealthElixir, ('Elixir of endurance', 'tiles/green-potion.png', 100)),
}
