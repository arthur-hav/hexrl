from combat import CombatInterface
from display import Interface, TextSprite, SimpleSprite, CascadeElement
from creatures import Creature
from pygame.locals import *
import choices
import random
import items
import json
import os


class EquipInterface(Interface, CascadeElement):
    def __init__(self, father, item):
        CascadeElement.__init__(self)
        self.item = item
        self.bg = SimpleSprite('helpmodal.png')
        self.bg.rect.x, self.bg.rect.y = 262, 200
        self.text = TextSprite('Apply to adventurer with [1-5]. [Esc] to cancel.', '#ffffff', 274, 250, maxlen=350)
        self.stats = TextSprite(str(item), '#ffffff', 274, 220, maxlen=350)
        self.subsprites = [self.bg, self.stats, self.text]
        Interface.__init__(self, father, keys = [
            (K_ESCAPE, lambda x: self.done()),
            ('[1-5]', self.equip),
            ])

    def equip(self, teamnum):
        if int(teamnum) >= len(self.father.pc_list):
            return
        self.item.equip(self.father.pc_list[int(teamnum) - 1])
        self.father.inventory.remove(self.item)
        self.done()

    def update(self, pos):
        self.father.update(pos)
        super().update(pos)
        self.display()


class MainMenuInterface(Interface, CascadeElement):
    def __init__(self):
        CascadeElement.__init__(self)
        self.bg = SimpleSprite('menu.png')
        self.hello = TextSprite('Choose a save slot with keys 1-3', '#ffffff', 320, 280)
        self.slots = []
        for i in range(3):
            try:
                slotname = 'Day %d' % json.load(open('save%d.json' % (i + 1)))['day']
            except FileNotFoundError:
                slotname = 'Empty'
            self.slots.append(TextSprite('[%d] Slot - %s' % (i + 1, slotname), '#ffffff', 320, 300 + 20 * i))
        self.subsprites = [self.bg, self.hello] + self.slots
        Interface.__init__(self, None, keys = [
            (K_ESCAPE, lambda x: self.done()),
            ('[1-3]', self.start),
            ])

    def start(self, slot):
        wi = WorldInterface(self)
        try:
            wi.load_game(int(slot))
        except FileNotFoundError as e:
            wi.new_game(int(slot))
        wi.activate()
        wi.display()
        self.desactivate()

    def on_return(self, defunct=None):
        for i in range(3):
            try:
                slotname = 'Day %d' % json.load(open('save%d.json' % (i + 1)))['day']
            except FileNotFoundError:
                slotname = 'Empty'
            self.slots[i].set_text('[%d] Slot - %s' % (i + 1, slotname))

    def update(self, mouse_pos):
        self.display()


class TeammateDisplay(CascadeElement):
    def __init__(self, creature, basex, basey):
        super().__init__()
        self.basex, self.basey = basex, basey
        self.pc = creature
        self.pc.rect.x, self.pc.rect.y = basex, basey
        self.health_stat = TextSprite('', '#ffffff', basex + 38, basey + 4)
        self.inventory = [
            SimpleSprite('icons/icon-blank.png'),
            SimpleSprite('icons/icon-blank.png'),
            SimpleSprite('icons/icon-blank.png'),
        ]
        for i, sprite in enumerate(self.inventory):
            sprite.rect.x, sprite.rect.y = basex + 120 + 32 * i, basey
        for i, item in enumerate(self.pc.items):
            item.rect.x, item.rect.y = self.inventory[i].rect.x, self.inventory[i].rect.y
        self.subsprites = [self.pc, self.health_stat] + self.inventory + self.pc.items

    def update(self):
        if self.pc.health < 0:
            self.must_show = False
        self.pc.rect.x, self.pc.rect.y = self.basex, self.basey
        self.health_stat.set_text("%s/%s" % (self.pc.health, self.pc.maxhealth))
        for item in self.pc.items:
            if item not in self.subsprites:
                self.subsprites.append(item)
        for item in self.subsprites[5:]:
            if item not in self.pc.items:
                self.subsprites.remove(item)
        for i, item in enumerate(self.pc.items):
            item.rect.x, item.rect.y = self.inventory[i].rect.x, self.inventory[i].rect.y


class StatusDisplay(CascadeElement):
    def __init__(self, worldinterface):
        super().__init__()
        self.worldinterface = worldinterface
        self.gold_icon = SimpleSprite('icons/gold.png')
        self.gold_icon.rect.x, self.gold_icon.rect.y = 20, 50
        self.gold_stat = TextSprite('', '#ffffff', 58, 54)
        self.day_text = TextSprite('', '#ffffff', 20, 90)
        self.inventory = []
        self.items = []
        for i in range(10):
            self.inventory.append(SimpleSprite('icons/icon-blank.png'))
            self.inventory[i].rect.x, self.inventory[i].rect.y = 50 + (i % 5) * 32, 380 + (i // 5) * 32
        self.subsprites = [self.gold_icon, self.gold_stat, self.day_text] + self.inventory
        self.teammates = []

    def update(self, mouse_pos):
        if not self.teammates:
            for i, pc in enumerate(self.worldinterface.pc_list):
                self.teammates.append(TeammateDisplay(pc, 20, 158 + 40 * i))
        self.gold_stat.set_text(str(self.worldinterface.party_gold))
        self.day_text.set_text("Day %d" % self.worldinterface.day)

        for pc in self.teammates:
            pc.update()

        for i, item in enumerate(self.worldinterface.inventory):
            item.rect.x, item.rect.y = self.inventory[i].rect.x, self.inventory[i].rect.y
            self.items.append(item)
        for item in self.items.copy():
            if item not in self.worldinterface.inventory:
                self.items.remove(item)
        self.subsprites = [self.gold_icon, self.gold_stat, self.day_text] + self.inventory + self.teammates + self.items

    def on_click(self, mouse_pos):
        for sprite in self.worldinterface.inventory:
            if sprite.rect.collidepoint(mouse_pos):
                ei = EquipInterface(self.worldinterface, sprite)
                ei.activate()
                ei.display()
                self.worldinterface.desactivate()
                return

        for pc in self.worldinterface.pc_list:
            for item in pc.items:
                if item.rect.collidepoint(mouse_pos):
                    item.unequip()
                    self.worldinterface.inventory.append(item)


class WorldInterface(Interface, CascadeElement):
    def __init__(self, father):
        CascadeElement.__init__(self)
        self.inventory_display = StatusDisplay(self)
        self.mob_list = []
        self.current_question_key = ''
        self.previous_question = ''
        self.current_question = None
        self.bg = SimpleSprite('menu.png')
        self.inventory = []
        self.cursor = SimpleSprite('icons/magnifyingglass.png')
        self.current_text = TextSprite('', '#ffffff', 320, 220, maxlen=300)
        self.choice_text = [TextSprite('', '#ffffff', 320, 400 + 16 * i) for i in range(4)] 
        self.subsprites = [self.bg, self.current_text, self.inventory_display] + self.choice_text + [self.cursor]
        self.formation = [ (-2, 4), (-1, 4.5), (0, 4), (1, 4.5), (2, 4), ]
        Interface.__init__(self, father, keys = [
            ('[1-4]', self.choose),
            (K_ESCAPE, self.quit),
            ])

    def on_return(self, defunct=None):
        if isinstance(defunct, CombatInterface):
            self.pick()
        self.pc_list = [pc for pc in self.pc_list if pc.health > 0]

    def on_click(self, mouse_pos):
        self.inventory_display.on_click(mouse_pos)

    def new_game(self, slot):
        self.slot = slot
        self.party_gold = 0
        self.day = 1
        self.this_day_question = 0
        self.questions_per_day = 4
        self.pc_list = [
            Creature('Fighter', is_pc=True),
            Creature('Barbarian', is_pc=True),
            Creature('Archer', is_pc=True),
            Creature('Wizard', is_pc=True),
            Creature('Enchantress', is_pc=True),
        ]
        self.pick()

    def pick(self):
        self.previous_question = self.current_question_key
        if not any((pc.health > 0 for pc in self.pc_list)):
            self.current_question_key = 'gameover'
        elif self.day == 1 and self.this_day_question == 0:
            self.current_question_key = 'start'
        elif self.this_day_question >= self.questions_per_day:
            self.current_question_key = 'rest'
        elif self.previous_question in ('gobelin_squad', 'undead'):
            self.current_question_key = 'loot'
        else:
            self.current_question_key = random.choice(list(choices.NORMAL_CHOICES.keys()))
        self.current_question = choices.get_question(self.current_question_key)(self)
        self.save_game()
        self.display_choices()

    def display_choices(self):
        for choice in self.choice_text:
            choice.set_text('')
        for key, val in enumerate(self.current_question.get_choices()):
            choice_text = "[%d] - %s" % (key + 1, val)
            self.choice_text[key].set_text(choice_text)
        self.current_text.set_text(self.current_question.get_text())

    def choose(self, key):
        key = int(key)
        if key > len(self.current_question.get_choices()):
            return
        if key == 1:
            self.current_question.choice_one()
        elif key == 2:
            self.current_question.choice_two()
        elif key == 3:
            self.current_question.choice_three()
        else:
            self.current_question.choice_four()

    def update(self, mouse_pos):
        self.inventory_display.update(mouse_pos)
        self.cursor.rect.x, self.cursor.rect.y = mouse_pos
        self.display()

    def start_combat(self, mobs):
        gi = CombatInterface(self, mobs)
        gi.activate()
        self.desactivate()

    def save_game(self):
        pc_dump = [pc.dict_dump()for pc in self.pc_list]
        inventory_dump = [item.name for item in self.inventory]
        save = {
                'pcs':pc_dump, 
                'gold':self.party_gold,
                'day': self.day,
                'questions_per_day': self.questions_per_day,
                'current_question': self.current_question_key,
                'rolls':self.current_question.dumps(),
                'previous_question': self.previous_question,
                'this_day_question': self.this_day_question,
                'inventory_dump': inventory_dump
                }
        with open('save%d.json' % self.slot, 'w') as f:
            f.write(json.dumps(save))

    def quit(self, mouse_pos):
        self.done()

    def erase_save(self):
        os.unlink('save%d.json' % self.slot)

    def load_game(self, slot):
        self.slot = slot
        with open('save%d.json' % slot) as f:
            d = json.loads(f.read())
        self.party_gold = d['gold']
        self.day = d['day']
        self.questions_per_day = d['questions_per_day']
        self.this_day_question = d['this_day_question']
        self.current_question_key = d['current_question']
        self.previous_question = d['previous_question']
        self.current_question = choices.get_question(self.current_question_key)(self)
        self.current_question.load(d['rolls'])
        for key in d['inventory_dump']:
            item_class = items.ITEMS[key][0]
            item_args = items.ITEMS[key][1]
            self.inventory.append(item_class(*item_args))
        self.pc_list = [Creature.dict_load(pc, self.inventory) for pc in d['pcs']]
        self.display_choices()

    def pay(self, amount):
        self.party_gold -= amount

    def next_question(self):
        self.previous_question = ''
        self.this_day_question += 1
        self.pick()

    def next_day(self):
        self.previous_question = ''
        self.this_day_question = 0
        self.day+= 1
        self.pick()

