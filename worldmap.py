from game import GameTile, GameInterface, Creature
from display import Display, Interface, TextSprite, SimpleSprite, CascadeElement, DISPLAY
from pygame.locals import *
import defs
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

class InventoryDisplay(CascadeElement):
    def __init__(self, worldinterface):
        self.worldinterface = worldinterface
        self.gold_icon = SimpleSprite('icons/gold.png')
        self.gold_icon.rect.x, self.gold_icon.rect.y = 754, 92
        self.gold_stat = TextSprite('', '#ffffff', 786, 100)
        self.subsprites = [self.gold_icon, self.gold_stat]

    def update(self, mouse_pos):
        self.gold_stat.set_text(str(self.worldinterface.party_gold))

class WorldInterface(Interface, CascadeElement):
    def __init__(self, father):
        self.inventory_display = InventoryDisplay(self)
        self.mob_list = []
        self.current_question = {}
        self.current_answer = {}
        self.bg = SimpleSprite('menu.png')
        self.current_text = TextSprite('', '#ffffff', 320, 220)
        self.choice_text = TextSprite('', '#ffffff', 320, 400)
        self.subsprites = [self.bg, self.current_text, self.choice_text, self.inventory_display]
        Interface.__init__(self, father, keys = [
            (K_KP1, lambda x: self.choose(0, x)),
            (K_KP2, lambda x: self.choose(1, x)),
            (K_KP3, lambda x: self.choose(2, x)),
            (K_ESCAPE, lambda x: self.save_game()),
            ])

    def on_return(self, defunct):
        if self.current_answer:
            self.current_answer['handler'].end(self)
        self.display()

    def new_game(self):
        self.party_gold = 0
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
            self.current_question = choices.GAMEOVER
        else:
            self.current_question = random.choice(choices.RANDOM_LIST)
        self.display_choices()

    def display_choices(self):
        choice_text = '\n'.join( ["%d - %s" % (key + 1, val['text']) for key, val in enumerate(self.current_question['choices'])])
        self.choice_text.set_text(choice_text)
        self.current_text.set_text(self.current_question['text'])

    def choose(self, key, tile):
        if key >= len(self.current_question['choices']):
            return
        self.current_answer = self.current_question['choices'][key]
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
        save = {'pcs':pc_dump, 'gold':self.party_gold}
        with open('save.json', 'w') as f:
            f.write(json.dumps(save))
        self.erase()
        self.done()

    def load_game(self, filename):
        with open(filename) as f:
            d = json.loads(f.read())
        self.party_gold = d['gold']
        self.pc_list = [Creature.dict_load(pc) for pc in d['pcs']]
        self.pick()

#this calls the 'main' function when this script is executed
if __name__ == '__main__':
    m = MainMenuInterface()
    m.activate()
    m.display()
    DISPLAY.main()
