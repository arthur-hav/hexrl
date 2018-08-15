import random
import os
import items

def get_question(key):
    if key in NORMAL_CHOICES:
        return NORMAL_CHOICES[key]
    return SPECIAL_CHOICES[key]

def exp_reward():
    i = 350
    while random.random() > 0.5:
        i += 350
    return random.randint(i, i + 350)

def exp_discount():
    i = 1100
    while random.random() > 0.5:
        i = int(i * 0.85)
    return random.randint(int(i*0.85), i)

class Choice():
    def __init__(self, world_interface):
        self.world_interface = world_interface
        self.rolls = []
        self.roll()
        self._init()

    def _init(self):
        pass

    def roll(self):
        pass

    def load(self, rolls):
        self.rolls = rolls
        self._init()

    def dumps(self):
        return self.rolls


class RestChoice(Choice):
    heal_percent = 30

    def get_text(self):
        s = 'You find a nice place to rest and settle a camp for the night.'
        for pc in self.world_interface.pc_list:
            if pc.health < pc.maxhealth:
                s += ' You take care of some of your wounds.'
                break
        return s

    def get_choices(self):
        return ['Rest']

    def choice_one(self):
        for cr in self.world_interface.pc_list:
            cr.health += 1 + int((cr.maxhealth - cr.health) * self.heal_percent / 100)
            cr.health = min(cr.health, cr.maxhealth)
        self.world_interface.next_day()

class GameOver(Choice):
    REWARD = 30
    def get_text(self):
        return 'Your are all dead...'
    def get_choices(self):
        return ['Back to main menu']
    def choice_one(self):
        os.unlink('save.json')
        self.world_interface.done()

class FightChoice(Choice):
    REWARD = 30
    def roll(self):
        self.rolls = [random.randint(2,7), random.randint(0,5)]
    def _init(self):
        self.mobs = [ ('Skeleton', (i, -4 + 0.5 * (i % 2))) for i in range(-self.rolls[0] // 2 + 1, self.rolls[0] // 2 + 1) ]
        self.mobs += [ ('SkeletonArcher', (i, -5 + 0.5 * (i % 2))) for i in range(-self.rolls[1] // 2 + 1, self.rolls[1] // 2 + 1) ] 
        if self.rolls[0] < 4:
            self.mobs.append(('Necromancer', (0, -6)))

    def get_text(self):
        return 'You find a pack of undead creatures. They are willing to make you join their army.'

    def get_choices(self):
        return ['Fight']
    def choice_one(self):
        return self.world_interface.start_game(self.mobs)

class DemonChoice(Choice):
    REWARD = 30
    def _init(self):
        self.mobs = [('Demon', (0, -6))]

    def get_text(self):
        return 'You encounter a major demon.'

    def get_choices(self):
        return ['Fight']
    def choice_one(self):
        return self.world_interface.start_game(self.mobs)


class TollChoice(FightChoice):
    REWARD = 20
    def roll(self):
        self.rolls = [exp_reward(), random.randint(3,5)]

    def _init(self):
        self.mobs = [ ('Gobelin', (i, -5 + 0.5 * (i % 2))) for i in range(-self.rolls[1] // 2 + 1, self.rolls[1] // 2 + 1) ]
        self.toll = self.rolls[0] // 50

    def get_text(self):
        return 'You are ambushed by a gobelin squad. They ask for a toll of %d gold.' % self.toll

    def get_choices(self):
        if self.world_interface.party_gold < self.toll:
            return ['Fight']
        return ['Fight', 'Pay the toll']

    def choice_two(self):
        self.world_interface.pay(self.toll)
        self.world_interface.current_question_key = ''
        self.world_interface.next_question()

class ShopChoice(Choice):
    def roll(self):
        self.rolls = [ random.choice( list(items.ITEMS.keys()) ), exp_discount() ]
    def _init(self):
        item_class = items.ITEMS[self.rolls[0]][0]
        item_args = items.ITEMS[self.rolls[0]][1]
        self.item = item_class(*item_args) 
        self.shop_price = self.rolls[1] * self.item.shop_price // 1000

    def get_text(self):
        if self.world_interface.party_gold < self.shop_price:
           return 'You found a shop, but everything it sells is way too expensive for you.'
        return 'You find a shop selling a shiny %s. You manage to bargain it for %d gold.' % (self.item.name, self.shop_price)

    def get_choices(self):
        if self.world_interface.party_gold < self.shop_price:
            return ['Leave']
        return ['Buy', 'Leave']

    def choice_one(self):
        if self.world_interface.party_gold < self.shop_price:
            self.world_interface.next_question()
        else:
            self.world_interface.party_gold -= self.shop_price
            self.world_interface.inventory.append(self.item)
            self.world_interface.next_question()

    def choice_two(self):
        self.world_interface.next_question()

class LootChoice(Choice):
    def roll(self):
        self.rolls = [exp_reward()]
    def _init (self):
        self.gold = get_question(self.world_interface.previous_question).REWARD * self.rolls[0] // 1000

    def get_text(self):
        return 'You scavenge valuables from the remains of your fight. They are worth %s gold.' % self.gold

    def get_choices(self):
        return ['Loot']

    def choice_one(self):
        self.world_interface.party_gold += self.gold
        self.world_interface.next_question()

class StartChoice(Choice):
    def roll(self):
        self.rolls = [exp_reward()]

    def get_text(self):
        return 'You start your adventure on the quest for the lost amulet of Yendor. Adventurers venture the land in the search for it as the king promised great wealth to whoever carried it back to him. You venture in the Lost lands, known for its great dangers...'

    def get_choices(self):
        return ['Start the journey']

    def choice_one(self):
        self.world_interface.party_gold += self.rolls[0] // 10
        self.world_interface.next_question()

NORMAL_CHOICES = {
    'gobelin_squad': TollChoice,
    'undead': FightChoice,
    'demon': DemonChoice,
    'shop': ShopChoice
}
SPECIAL_CHOICES = {
    'rest':RestChoice,
    'start':StartChoice,
    'gameover':GameOver,
    'loot':LootChoice,
}
