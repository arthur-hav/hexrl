from game import GameTile, GameInterface, Creature
from display import Display, Interface, TextSprite, SimpleSprite, CascadeElement, DISPLAY
from pygame.locals import *
import choices
import random
import items
import json
import os

class EquipInterface(Interface, CascadeElement):
    def __init__(self, father, item):
        self.item = item
        self.bg = SimpleSprite('helpmodal.png')
        self.bg.rect.x, self.bg.rect.y = 262, 200
        self.text = TextSprite('Equip which adventurer ? [1-5]', '#ffffff', 274, 220)
        self.stats = TextSprite(str(item), '#ffffff', 274, 240, maxlen=350)
        self.subsprites = [self.bg, self.stats, self.text]
        Interface.__init__(self, father, keys = [
            (K_ESCAPE, lambda x: self.done()),
            ('1', lambda x: self.equip(0)),
            ('2', lambda x: self.equip(1)),
            ('3', lambda x: self.equip(2)),
            ('4', lambda x: self.equip(3)),
            ('5', lambda x: self.equip(4)),
            ])
    def equip(self, teamnum):
        if teamnum > len(self.father.pc_list):
            return
        self.item.equip(self.father.pc_list[teamnum])
        self.erase()
        self.done()

class MainMenuInterface(Interface, CascadeElement):
    def __init__(self):
        self.bg = SimpleSprite('menu.png')
        self.hello = TextSprite('Press <Enter> to start the game...', '#ffffff', 320, 280)
        self.subsprites = [self.bg, self.hello]
        Interface.__init__(self, None, keys = [
            (K_ESCAPE, lambda x: self.done()),
            (K_RETURN, self.start),
            ])

    def start(self, mouse_pos):
        self.erase()
        wi = WorldInterface(self)
        if os.path.exists('save.json'):
            wi.load_game('save.json')
        else:
            wi.new_game()
        wi.activate()
        wi.display()
        self.desactivate()

    def on_return(self, defunct):
        self.display()

class StatusDisplay(CascadeElement):
    def __init__(self, worldinterface):
        self.worldinterface = worldinterface
        self.gold_icon = SimpleSprite('icons/gold.png')
        self.gold_icon.rect.x, self.gold_icon.rect.y = 754, 92
        self.gold_stat = TextSprite('', '#ffffff', 786, 100)
        self.day_text = TextSprite('', '#ffffff', 786, 132)
        self.inventory = [] 
        for i in range(20):
            self.inventory.append(SimpleSprite('icons/icon-blank.png'))
            self.inventory[i].rect.x, self.inventory[i].rect.y = 754 + (i % 4) * 32, 350 + (i // 4) * 32
        self.subsprites = [self.gold_icon, self.gold_stat, self.day_text] + self.inventory
        self.health_stats = []
        self.pc_icons = []
        for i in range(5):
            pc_tile = SimpleSprite('tiles/Skeleton.png')
            pc_tile.rect.x, pc_tile.rect.y = 754, 158 + 32 * i
            pc_health_stat = TextSprite('', '#ffffff', 786, 164 + 32 * i)
            self.health_stats.append(pc_health_stat)
            self.pc_icons.append(pc_tile)
            self.subsprites.extend([pc_tile, pc_health_stat])

    def update(self, mouse_pos):
        self.subsprites = [self.gold_icon, self.gold_stat, self.day_text] + self.inventory
        self.item_sprites = []
        self.gold_stat.set_text(str(self.worldinterface.party_gold))
        for i, pc in enumerate(self.worldinterface.pc_list):
            self.health_stats[i].set_text("%s/%s" % (pc.health, pc.maxhealth))
            self.day_text.set_text("Day %d" % self.worldinterface.day)
            self.pc_icons[i].animate(pc.image_name)
            self.subsprites.append(self.pc_icons[i])
        for i, item in enumerate(self.worldinterface.inventory):
            if item.equipped_to:
                self.inventory[i].animate('tiles/Green2.png')
            item.rect.x, item.rect.y = self.inventory[i].rect.x, self.inventory[i].rect.y
            self.subsprites.append(item)
        self.display()

    def on_click(self, mouse_pos):
        for sprite in self.worldinterface.inventory:
            if sprite.rect.collidepoint(mouse_pos):
                ei = EquipInterface(self.worldinterface, sprite)
                ei.activate()
                ei.display()
                self.worldinterface.desactivate()
                break

class WorldInterface(Interface, CascadeElement):
    def __init__(self, father):
        self.inventory_display = StatusDisplay(self)
        self.mob_list = []
        self.current_question_key = ''
        self.previous_question = ''
        self.current_question = None
        self.bg = SimpleSprite('menu.png')
        self.inventory = []
        self.current_text = TextSprite('', '#ffffff', 320, 220, maxlen=300)
        self.choice_text = [TextSprite('', '#ffffff', 320, 400 + 16 * i) for i in range(3)] 
        self.subsprites = [self.bg, self.current_text, self.inventory_display] + self.choice_text
        Interface.__init__(self, father, keys = [
            ('1', lambda x: self.choose(0, x)),
            ('2', lambda x: self.choose(1, x)),
            ('3', lambda x: self.choose(2, x)),
            (K_ESCAPE, self.quit),
            ])

    def on_return(self, defunct):
        self.display()
        if isinstance(defunct, GameInterface):
            self.pick()

    def on_click(self, mouse_pos):
        self.inventory_display.on_click(mouse_pos)

    def new_game(self):
        self.party_gold = 0
        self.day = 1
        self.this_day_question = 0
        self.questions_per_day = 4
        self.pc_list = [
            Creature('Fighter', is_pc=True),
            Creature('Barbarian', is_pc=True),
            Creature('Archer', is_pc=True),
            Creature('Wizard', is_pc=True),
            Creature('Archer', is_pc=True),
        ]
        self.pick()

    def pick (self):
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

    def choose(self, key, tile):
        if key >= len(self.current_question.get_choices()):
            return
        if key == 0:
            self.current_question.choice_one()
        elif key == 1:
            self.current_question.choice_two()
        else:
            self.current_question.choice_three()

    def update(self, mouse_pos):
        self.inventory_display.update(mouse_pos)

    def start_game(self, mobs):
        self.erase()
        gi = GameInterface(self, mobs)
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
        with open('save.json', 'w') as f:
            f.write(json.dumps(save))

    def quit(self, mouse_pos):
        self.erase()
        self.done()

    def load_game(self, filename):
        with open(filename) as f:
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

#this calls the 'main' function when this script is executed
if __name__ == '__main__':
    m = MainMenuInterface()
    m.activate()
    m.display()
    DISPLAY.main()

