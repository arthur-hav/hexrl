from game import GameTile, GameInterface, Creature
from display import Display, Interface
from pygame.locals import *
import defs

class MainMenuInterface(Interface):
    def __init__(self, display):
        super(MainMenuInterface, self).__init__(None, display, 'menu.png', keys = [
            (K_ESCAPE, self.done),
            (K_RETURN, self.start),
            ])
    def start(self, key):
        WorldInterface(self)

class WorldInterface(Interface):
    def __init__(self, father):
        self.pc_list = [
            Creature(defs.PC1),
            Creature(defs.PC2),
            Creature(defs.PC1),
            Creature(defs.PC2),
            Creature(defs.PC1),
        ]
        super(WorldInterface, self).__init__(father, father.display, 'worldmap.png', keys = [
            (K_RETURN, self.go),
            ])

    def go(self, tile):
        self.start_game()

    def start_game(self):
        gi = GameInterface(self)

#this calls the 'main' function when this script is executed
if __name__ == '__main__':
    d = Display()
    m = MainMenuInterface(d)
    d.main()
