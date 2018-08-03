from game import GameTile, GameInterface, Creature
from display import Display, Interface, TextSprite
from pygame.locals import *
import defs
import choices
import random

class MainMenuInterface(Interface):
    def __init__(self, display):
        super(MainMenuInterface, self).__init__(None, display, 'menu.png', keys = [
            (K_ESCAPE, self.done),
            (K_RETURN, self.start),
            ])

    def start(self, key):
        self.hello.erase()
        WorldInterface(self)

    def activate(self):
        super(MainMenuInterface, self).activate()
        self.hello = TextSprite('Press <Enter> to start the game...', '#ffffff', 320, 280)



class WorldInterface(Interface):
    def __init__(self, father):
        self.pc_list = [
            Creature(defs.PC1),
            Creature(defs.PC2),
            Creature(defs.PC1),
            Creature(defs.PC2),
            Creature(defs.PC1),
        ]
        self.party_gold = 0
        self.mob_list = []
        super(WorldInterface, self).__init__(father, father.display, 'worldmap.png', keys = [
            (K_KP1, lambda x: self.choose(0, x)),
            (K_KP2, lambda x: self.choose(1, x)),
            (K_KP3, lambda x: self.choose(2, x)),
            ])

    def activate(self):
        super(WorldInterface, self).activate()
        self.current_choice = random.choice(choices.RANDOM_LIST)
        if not any((pc.health > 0 for pc in self.pc_list)):
            self.current_choice = choices.GAMEOVER

        self.current_text = TextSprite(self.current_choice['text'], '#ffffff', 320, 280)
        self.choices_text = [ TextSprite("%d - %s" % (key + 1, self.current_choice['choices'][key]['text']),
            '#ffffff', 320, 320 + 20 * key) for key in range(len(self.current_choice['choices'])) ]


    def choose(self, key, tile):
        if key >= len(self.current_choice['choices']):
            return
        if self.current_choice['choices'][key]['type'] == 'fight':
            self.mob_list = self.current_choice['choices'][key]['mobs']
            self.start_game()
        if self.current_choice['choices'][key]['type'] == 'gameover':
            self.erase_all()
            self.done()

    def erase_all(self):
        self.current_text.erase()
        for choice in self.choices_text:
            choice.erase()

    def start_game(self):
        self.erase_all()
        gi = GameInterface(self)

#this calls the 'main' function when this script is executed
if __name__ == '__main__':
    d = Display()
    m = MainMenuInterface(d)
    d.main()
