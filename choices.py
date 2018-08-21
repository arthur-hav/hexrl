import random
import items
from pygame.locals import *
from display import Interface, SimpleSprite, TextSprite, CascadeElement


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


class Choice:
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
    heal_percent = 25

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
        self.world_interface.erase_save()
        self.world_interface.done()


class FightChoice(Choice):
    REWARD = 30

    def roll(self):
        self.rolls = [random.randint(2,7), random.randint(0,5)]

    def _init(self):
        self.mobs = [ ('Skeleton', (i, -4 + 0.5 * (i % 2))) for i in range(-self.rolls[0] // 2 + 1, self.rolls[0] // 2 + 1) ]
        self.mobs += [ ('SkeletonArcher', (i, -5 + 0.5 * (i % 2))) for i in range(-self.rolls[1] // 2 + 1, self.rolls[1] // 2 + 1) ] 

    def get_text(self):
        return 'You find a pack of undead creatures. They want to make you join their army.'

    def get_choices(self):
        return ['Fight']

    def choice_one(self):
        return self.world_interface.start_combat(self.mobs)


class OldManChoice(Choice):
    def roll(self):
        self.rolls = [random.randint(0,1)]

    def get_text(self):
        return 'You see an old man far in the mist. Do you want to go greet him ?'

    def get_choices(self):
        return ['Yes', 'No']

    def choice_one(self):
        if self.rolls[0]:
            self.world_interface.current_question = get_question('necromancer')(self.world_interface)
            self.world_interface.save_game()
            self.world_interface.display_choices()
        else:
            self.world_interface.current_question = get_question('goodoldman')(self.world_interface)
            self.world_interface.save_game()
            self.world_interface.display_choices()

    def choice_two(self):
        self.world_interface.next_question()

class NecromancerChoice(Choice):

    def roll(self):
        self.rolls = [random.randint(4,7)]

    def _init(self):
        self.mobs = [ ('Skeleton', (i, -5 + 0.5 * (i % 2))) for i in range(-self.rolls[0] // 2 + 1, self.rolls[0] // 2 + 1) ]
        self.mobs.append(('Necromancer', (0, -6)))

    def get_text(self):
        return 'As you come further, other shadows rises from your sides. He is certainly no ordinary old man...'

    def get_choices(self):
        return ['Fight']

    def choice_one(self):
        return self.world_interface.start_combat(self.mobs)


class GoodOldManChoice(Choice):

    def roll(self):
        self.rolls = [random.choice( list(items.ITEMS.keys()))]

    def get_text(self):
        return 'As you greet him, the old man tells you he is lost and leaves in a nearby village. ' \
               'You accompany him to safety. He thanks you warmly and offer you an item to show you his gratitude.'

    def get_choices(self):
        return ['OK']

    def choice_one(self):
        item_class = items.ITEMS[self.rolls[0]][0]
        item_args = items.ITEMS[self.rolls[0]][1]
        item = item_class(*item_args)
        self.world_interface.inventory.append(item)
        self.world_interface.next_question()


class BansheeChoice(Choice):

    def roll(self):
        self.rolls = [random.randint(5, 7)]

    def _init(self):
        self.mobs = [('Banshee', (i, -5 + 0.5 * (i % 2))) for i in range(-self.rolls[0] // 2 + 1, self.rolls[0] // 2 + 1)]

    def get_text(self):
        return 'You hear screams that tell you no good. Adventurers watch each others in terror, as they know ' \
               'what is coming next. They are called the Banshees.'

    def get_choices(self):
        return ['Fight']

    def choice_one(self):
        return self.world_interface.start_combat(self.mobs)

class DemonChoice(Choice):
    REWARD = 30

    def _init(self):
        self.mobs = [('Demon', (0, -6))]

    def get_text(self):
        return 'You encounter a major demon.'

    def get_choices(self):
        return ['Fight']

    def choice_one(self):
        return self.world_interface.start_combat(self.mobs)


class TollChoice(Choice):
    REWARD = 20

    def roll(self):
        self.rolls = [exp_reward(), random.randint(3,5)]

    def _init(self):
        self.mobs = [ ('Gobelin', (i, -5 + 0.5 * (i % 2))) for i in range(-self.rolls[1] // 2 + 1, self.rolls[1] // 2 + 1) ]
        self.mobs.append(('Troll', (0, -6)))
        self.toll = self.rolls[0] // 50

    def get_text(self):
        return 'You are ambushed by a gobelin squad. They ask for a toll of %d gold.' % self.toll

    def get_choices(self):
        if self.world_interface.party_gold < self.toll:
            return ['Fight']
        return ['Fight', 'Pay the toll']

    def choice_one(self):
        return self.world_interface.start_combat(self.mobs)

    def choice_two(self):
        self.world_interface.pay(self.toll)
        self.world_interface.current_question_key = ''
        self.world_interface.next_question()

class ShopChoice(Choice):

    def roll(self):
        self.rolls = [ random.choice( list(items.ITEMS.keys()) ) for _ in range(3)] + [exp_discount() for _ in range(3)]

    def _init(self, first=True):
        self.items = []
        self.prices = []
        self.first = first
        for i in range(3):
            item_class = items.ITEMS[self.rolls[i]][0]
            item_args = items.ITEMS[self.rolls[i]][1]
            item = item_class(*item_args)
            price = self.rolls[i + 3] * item.shop_price // 1000
            if price < self.world_interface.party_gold:
                self.prices.append(price)
                self.items.append(item)

    def get_text(self):
        if self.items:
           return 'You found a shop selling a few valuable items.'
        if self.first:
           return 'You found a shop, sadly everything it sells is too expensive for you.'
        return 'You shopped everything you could and must leave.'

    def get_choices(self):
        choices = []
        for item, price in zip(self.items, self.prices):
            choices.append('Buy %s for %d gold' % (item.name, price))
        choices.append('Leave')
        return choices

    def choice(self, num):
        if num >= len(self.items):
            self.world_interface.next_question()
            return
        self.world_interface.party_gold -= self.prices[num]
        self.world_interface.inventory.append(self.items[num])
        self._init(False)
        self.world_interface.display_choices()

    def choice_one(self):
        self.choice(0)

    def choice_two(self):
        self.choice(1)

    def choice_three(self):
        self.choice(2)

    def choice_four(self):
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


class NothingChoice(Choice):
    TEXTS = [
        "The sun softly warms your skin as you keep walking. You pass beneath a beautiful tree. You feel at ease.",
        "As the mist thickens you mark a pause on your journey to avoid dangerous ambushes, but nothing bad happens.",
        "During your walk, adventurers argue about possible meanings of life.",
    ]

    def roll(self):
        self.rolls = [random.choice(NothingChoice.TEXTS)]

    def _init (self):
        pass

    def get_text(self):
        return self.rolls[0]

    def get_choices(self):
        return ['OK']

    def choice_one(self):
        self.world_interface.next_question()


class TavernModal(Interface, CascadeElement):
    def __init__(self, father, tavern):
        CascadeElement.__init__(self)
        self.bg = SimpleSprite('helpmodal.png')
        self.bg.rect.x, self.bg.rect.y = 262, 200
        self.text = TextSprite('Enter a word or two about your inquiry', '#ffffff', 274, 250)
        self.question = TextSprite('', '#ffffff', 274, 300)
        self.word = ''
        self.tavern = tavern
        self.subsprites = [self.bg, self.text, self.question]
        Interface.__init__(self, father, keys = [
            (K_ESCAPE, lambda x: self.done()),
            ('[a-z ]', self.typing),
            (K_BACKSPACE, self.erase),
            (K_RETURN, self.validate),
            ])

    def typing(self, code):
        self.word += code
        self.question.set_text(self.word)
    
    def erase(self, _):
        self.word = self.word[:-1]
        self.question.set_text(self.word)

    def validate(self, _):
        self.tavern.inquiry(self.word)
        self.done()

    def update(self, mouse_pos):
        self.display()


class TavernChoice(Choice):
    ANSWERS = { 
            'name': 'My name is Barnabas',
            'job': 'I run the tavern, of course ! If you wonder, the business is going fairly well you may say.',
            'old man': 'Take care, some are not what they seem to be.',
            'gobelins': 'Such a plague they are, damn right',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = "You enter a small tavern where you can gather information. " \
                    "You sit at the bar. The barman looks friendly and waits for you to order a drink."

    def inquiry(self, word):
        self.text = self.ANSWERS.get(word, 'eh ?')
        self.world_interface.display_choices()

    def get_text(self):
        return self.text

    def get_choices(self):
        return ['Ask...', 'Leave']

    def choice_one(self):
        t = TavernModal(self.world_interface, self)
        self.world_interface.desactivate()
        t.activate()

    def choice_two(self):
        self.world_interface.next_question()


class StartChoice(Choice):
    def roll(self):
        self.rolls = [exp_reward()]

    def get_text(self):
        return 'You start your adventure on the quest for the lost amulet of Yendor. ' \
               'Adventurers venture the land in the search for it as the king promised great wealth to whoever ' \
               'carried it back to him. You venture in the Lost lands, known for its great dangers...'

    def get_choices(self):
        return ['Start the journey']

    def choice_one(self):
        self.world_interface.party_gold += self.rolls[0] // 10
        self.world_interface.next_question()


NORMAL_CHOICES = {
    'gobelin_squad': TollChoice,
    'undead': FightChoice,
    'demon': DemonChoice,
    'nothing': NothingChoice,
    'oldman': OldManChoice,
    'shop': ShopChoice,
    'tavern': TavernChoice,
    'banshee': BansheeChoice
}
SPECIAL_CHOICES = {
    'rest': RestChoice,
    'necromancer': NecromancerChoice,
    'goodoldman': GoodOldManChoice,
    'start': StartChoice,
    'gameover': GameOver,
    'loot': LootChoice,
}
