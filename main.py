from display import DISPLAY
from worldmap import MainMenuInterface

if __name__ == '__main__':
    DISPLAY.setup()
    m = MainMenuInterface()
    m.activate()
    m.display()
    DISPLAY.main()

