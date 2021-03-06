#!/usr/bin/env python

#Import Modules
import os, pygame
import re
from pygame.locals import *
from pygame.compat import geterror
import sys
import time
from collections import defaultdict

#custom module containing card database

 
if not pygame.font: 
    sys.exit("Fonts unavailable, cannot start. Try installing SDL_ttf")
if not pygame.mixer: 
    print ('Warning, sound disabled')


class Display:
    def __init__(self):
        #Initialize Everything
        self.key_handlers = defaultdict(list)
        self.mouse_handlers = []
        self.update_handlers = []
        self.sprites = pygame.sprite.OrderedUpdates(())

        #clock = pygame.time.Clock()

    def subscribe_key(self, key, eventhandler):
        self.key_handlers[key].append(eventhandler)

    def subscribe_click(self, eventhandler):
        self.mouse_handlers.append(eventhandler)

    def subscribe_update(self, eventhandler):
        self.update_handlers.append(eventhandler)

    def unsubscribe_key(self, key, eventhandler):
        self.key_handlers[key].remove(eventhandler)

    def unsubscribe_click(self, eventhandler):
        self.mouse_handlers.remove(eventhandler)

    def unsubscribe_update(self, eventhandler):
        self.update_handlers.remove(eventhandler)

    def setup(self):
        pygame.init()
        self.screen = pygame.display.set_mode((960, 600)) #, pygame.FULLSCREEN|pygame.HWSURFACE)
        pygame.mouse.set_visible(False)
        pygame.display.set_caption('HexRL')
        #pygame.mouse.set_visible(0)
        #Display The Background
        pygame.display.flip()

    def handle_key(self, key, unicode):
        for k, handlers in list(self.key_handlers.items()):
            for handler in handlers:
                if (isinstance(k, str) and re.match(k, unicode)) or k == key:
                    handler(unicode)

    def main(self):
        pressed_dirs = set()
        while True:
            pygame.display.flip()
            # Handle Input Events
            pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == QUIT:
                    exit(0)
                elif event.type == KEYDOWN:
                    if event.key in (K_DOWN, K_UP, K_LEFT, K_RIGHT):
                        pressed_dirs.add(event.key)
                    else:
                        self.handle_key(event.key, event.unicode)
                elif event.type == KEYUP:
                    if len(pressed_dirs) == 1 and event.key == K_DOWN:
                        self.handle_key(event.key, 'down')
                    elif len(pressed_dirs) == 1 and event.key == K_UP:
                        self.handle_key(event.key, 'up')
                    elif event.key in (K_DOWN, K_UP, K_LEFT, K_RIGHT):
                        direction = None
                        if K_DOWN in pressed_dirs and K_LEFT in pressed_dirs:
                            direction = "downleft"
                        elif K_DOWN in pressed_dirs and K_RIGHT in pressed_dirs:
                            direction = "downright"
                        elif K_UP in pressed_dirs and K_LEFT in pressed_dirs:
                            direction = "upleft"
                        elif K_UP in pressed_dirs and K_RIGHT in pressed_dirs:
                            direction = "upright"
                        if direction:
                            pressed_dirs = set()
                            self.handle_key(event.key, direction)
                    if event.key in pressed_dirs:
                        pressed_dirs.remove(event.key)
                elif event.type == MOUSEBUTTONDOWN:
                    for handler in self.mouse_handlers:
                        handler(pos)
                elif event.type == MOUSEMOTION:
                    pass
                elif event.type == MOUSEBUTTONUP:
                    pass
            for handler in self.update_handlers:
                handler(pos)
            time.sleep(0.020)


DISPLAY = Display()


def load_sound(name):
    class NoneSound:
        def play(self):
            pass
    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    data_dir = os.path.join(main_dir, 'data')
    fullname = os.path.join(data_dir, name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error:
        print ('Cannot load sound: %s' % fullname)
        raise SystemExit(str(geterror()))
    return sound

#    whiff_sound = load_sound('whiff.wav')
#    whiff_sound.play()


class CascadeElement:
    def __init__(self, subsprites=[]):
        self.subsprites = subsprites
        self.must_show = True

    def display(self):
        if not self.must_show:
            return
        for sprite in self.subsprites:
            sprite.display()


class SimpleSprite (pygame.sprite.Sprite):
    """ Simple sprites refreshed every frame."""
    #functions to create our resources
    loaded_images = {}
    @staticmethod
    def load_image(name):
        main_dir = os.path.split(os.path.abspath(__file__))[0]
        data_dir = os.path.join(main_dir, 'data')
        fullname = os.path.join(data_dir, name)
        if fullname in SimpleSprite.loaded_images:
            return SimpleSprite.loaded_images[fullname]
        try:
            image = pygame.image.load(fullname)
            SimpleSprite.loaded_images[fullname] = image
        except pygame.error:
            print ('Cannot load image:', fullname)
            raise SystemExit(str(geterror()))
        return image

    def __init__(self, image_name):
        super(SimpleSprite, self).__init__()
        self.image = self.load_image(image_name)
        rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (rect.w * 2, rect.h * 2)) 
        self.rect = self.image.get_rect()
        self.frame_name = image_name
        self.must_show = True

    def move_to(self, x, y):
        self.rect.x, self.rect.y = x, y

    def display(self):
        if self.must_show:
            DISPLAY.screen.blit(self.image, self.rect)
    
    def animate(self, frame_name):
        if frame_name == self.frame_name:
            return
        self.image = SimpleSprite.load_image(frame_name)
        rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (rect.w * 2, rect.h * 2)) 
        self.frame_name = frame_name


class Gauge(pygame.sprite.Sprite):
    def __init__(self, width, height, color):
        """Can be used for either vertical or horizontal gauge"""
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image = pygame.Surface((width, height))
        self.height = height
        self.width = width
        self.color = color
        self.rect = self.image.get_rect()
        self.image.fill(pygame.Color(color))
        self.must_show = True

    def move_to(self, x, y):
        self.rect.x, self.rect.y = x, y

    def display(self):
        if self.must_show:
            DISPLAY.screen.blit(self.image, self.rect)

    def set_width (self, size):
        self.image = pygame.Surface((size, self.height))
        self.image.fill(pygame.Color(self.color))
        self.width = size

    def set_height (self, size):
        self.image = pygame.Surface((self.width, size))
        self.image.fill(pygame.Color(self.color))
        self.height = size


class TextSprite:
    """ Text sprites, can be re-used through set_text """
    def __init__ (self, text, color, x=0, y=0, maxlen=None):
        self.font = pygame.font.Font("data/font/Vera.ttf", 8)
        self.color = [color] if isinstance(color, str) else color
        self.maxlen = maxlen
        self.x = x
        self.y = y
        self.textsprites = []
        self.must_show = True
        self._render(text)

    def _render(self, text):
        words = text.split(' ')
        i = 0
        j = 0
        for word in words:
            sprite = pygame.sprite.Sprite()
            sprite.image = self.font.render(word, False, pygame.Color(*self.color))
            (w, h) = self.font.size (word)
            sprite.image = pygame.transform.scale(sprite.image, (w * 2, h * 2)) 
            sprite.rect = pygame.Rect (self.x + i, self.y + j, w, h)
            self.textsprites.append(sprite)
            i += w * 2 + 6
            if self.maxlen and i > self.maxlen:
                i = 0
                j += 16

    def set_text (self, text):
        if self.textsprites:
            self.textsprites = []
        self._render(text)

    def display(self):
        if not self.must_show:
            return
        for sprite in self.textsprites:
            DISPLAY.screen.blit(sprite.image, sprite.rect)


class Interface:
    """Represents a scene, or a window modal, listening to events and
    eventually returning to a parent window."""
    def __init__(self, father, keys=[]):
        self.father = father
        self.keys = keys

    def desactivate(self):
        DISPLAY.unsubscribe_click(self.on_click)
        DISPLAY.unsubscribe_update(self.update)
        for k, v in self.keys:
            DISPLAY.unsubscribe_key(k, v)

    def activate(self):
        DISPLAY.subscribe_click(self.on_click)
        DISPLAY.subscribe_update(self.update)
        for k, v in self.keys:
            DISPLAY.subscribe_key(k, v)

    def on_return(self, defunct=None):
        pass

    def update(self, pos):
        pass
    
    def on_click(self, pos):
        pass

    def done(self):
        self.desactivate()
        if self.father:
            self.father.activate()
            self.father.on_return(self)
        else:
            exit(0)


