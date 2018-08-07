from game import GameTile, GameInterface, Creature
from display import Display, Interface, TextSprite, SimpleSprite, CascadeElement, DISPLAY
from pygame.locals import *
import choices
import random
import json
import os

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
        self.subsprites = [self.gold_icon, self.gold_stat]
        self.health_stats = []
        self.pc_icons = []
        for i in range(5):
            pc_tile = SimpleSprite('tiles/Skeleton.png')
            pc_tile.rect.x, pc_tile.rect.y = 754, 124 + 32 * i
            pc_health_stat = TextSprite('', '#ffffff', 786, 132 + 32 * i)
            self.health_stats.append(pc_health_stat)
            self.pc_icons.append(pc_tile)
            self.subsprites.extend([pc_tile, pc_health_stat])

    def update(self, mouse_pos):
        self.gold_stat.set_text(str(self.worldinterface.party_gold))
        for i, pc in enumerate(self.worldinterface.pc_list):
            self.health_stats[i].set_text("%s/%s" % (pc.health, pc.maxhealth))
            self.pc_icons[i].animate(pc.image_name)

class WorldInterface(Interface, CascadeElement):
    def __init__(self, father):
        self.inventory_display = StatusDisplay(self)
        self.mob_list = []
        self.current_question = ''
        self.previous_question = ''
        self.current_answer = {}
        self.bg = SimpleSprite('menu.png')
        self.current_text = TextSprite('', '#ffffff', 320, 220, maxlen=300)
        self.choice_text = [TextSprite('', '#ffffff', 320, 400)] * 3
        self.subsprites = [self.bg, self.current_text, self.inventory_display] + self.choice_text
        Interface.__init__(self, father, keys = [
            ('1', lambda x: self.choose(0, x)),
            ('2', lambda x: self.choose(1, x)),
            ('3', lambda x: self.choose(2, x)),
            (K_ESCAPE, lambda x: self.save_game()),
            ])

    def on_return(self, defunct):
        self.display()
        self.pick()

    def new_game(self):
        self.party_gold = 0
        self.day = 1
        self.this_day_question = 0
        self.questions_per_day = 3 
        self.pc_list = [
            Creature('Fighter'),
            Creature('Barbarian'),
            Creature('Archer'),
            Creature('Barbarian'),
            Creature('Archer'),
        ]
        self.pick()

    def pick (self):
        if not any((pc.health > 0 for pc in self.pc_list)):
            self.current_question = 'gameover'
        elif self.day == 1 and self.this_day_question == 0:
            self.current_question = 'start'
        elif self.this_day_question > self.questions_per_day:
            self.current_question = 'rest'
        elif self.previous_question in ('gobelin_squad', 'undead'):
            self.current_question = 'loot'
        else:
            self.current_question = random.choice(list(choices.NORMAL_CHOICES.keys()))
        self.previous_question = self.current_question
        self.display_choices()

    def display_choices(self):
        question = choices.get_question(self.current_question)
        for key, val in enumerate(question['choices']):
            choice_text = "[%d] - %s" % (key + 1, val['text'])
            self.choice_text[key].set_text(choice_text)
        self.current_text.set_text(question['text'])

    def choose(self, key, tile):
        question = choices.get_question(self.current_question)
        if key >= len(question['choices']):
            return
        self.current_answer = question['choices'][key]
        self.current_answer['handler'].start(self)

    def update(self, mouse_pos):
        self.inventory_display.update(mouse_pos)

    def start_game(self):
        self.erase()
        gi = GameInterface(self)
        gi.activate()
        self.desactivate()

    def save_game(self):
        pc_dump = [pc.dict_dump()for pc in self.pc_list]
        save = {
                'pcs':pc_dump, 
                'gold':self.party_gold,
                'day': self.day,
                'questions_per_day': self.questions_per_day,
                'current_question': self.current_question,
                'previous_question': self.previous_question,
                'this_day_question': self.this_day_question
                }
        with open('save.json', 'w') as f:
            f.write(json.dumps(save))
        self.erase()
        self.done()

    def load_game(self, filename):
        with open(filename) as f:
            d = json.loads(f.read())
        self.party_gold = d['gold']
        self.day = d['day']
        self.questions_per_day = d['questions_per_day']
        self.this_day_question = d['this_day_question']
        self.current_question = d['current_question']
        self.previous_question = d['previous_question']
        self.pc_list = [Creature.dict_load(pc) for pc in d['pcs']]
        #self.pick()
        self.display_choices()

#this calls the 'main' function when this script is executed
if __name__ == '__main__':
    m = MainMenuInterface()
    m.activate()
    m.display()
    DISPLAY.main()
