#!/usr/bin/env python

#Import Modules
import os, pygame
from pygame.locals import *
from pygame.compat import geterror
import sys
import time
from collections import defaultdict

#custom module containing card database

 
if not pygame.font: print ('Warning, fonts disabled')
if not pygame.mixer: print ('Warning, sound disabled')


main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')


def load_sound(name):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join(data_dir, name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error:
        print ('Cannot load sound: %s' % fullname)
        raise SystemExit(str(geterror()))
    return sound

#    whiff_sound = load_sound('whiff.wav')
#    whiff_sound.play() 

#        pos = pygame.mouse.get_pos()
#        self.rect.midtop = pos
#            self.rect.move_ip(5, 10)

#            hitbox = self.rect.inflate(-5, -5)
#            return hitbox.colliderect(target.rect)

#        newpos = self.rect.move((self.move, 0))
#            self.image = pygame.transform.flip(self.image, 1, 0)

        #center = self.rect.center
            #rotate = pygame.transform.rotate
            #self.image = rotate(self.original, self.dizzy)
        #self.rect = self.image.get_rect(center=center)

ALL_SPRITES = [pygame.sprite.LayeredUpdates(()) for i in range(10)]

#classes for our game objects

class SimpleSprite (pygame.sprite.Sprite):
    """ Simple sprites refreshed every frame """
    #functions to create our resources
    loaded_images = {}
    @staticmethod
    def load_image(name, colorkey=None):
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

    def __init__(self, image_name, flipped=False, layer=5):
        super(SimpleSprite, self).__init__()
        self.image = self.load_image(image_name)
        rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (rect.w * 2, rect.h * 2)) 
        self.rect = self.image.get_rect()
        self.layer = layer
        ALL_SPRITES[layer].add (self)
    
    def animate(self, frame_name):
        self.image = SimpleSprite.load_image(frame_name)
        rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (rect.w * 2, rect.h * 2)) 

    def erase (self):
        ALL_SPRITES[self.layer].remove (self)

class Gauge(pygame.sprite.Sprite):
    def __init__(self, height, size, color, layer=5):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image = pygame.Surface((size, height))
        self.height = height
        self.color = color
        self.rect = self.image.get_rect()
        self.layer = layer
        self.image.fill(pygame.Color(color))
        ALL_SPRITES[layer].add (self)

    def set_size (self, size):
        self.image = pygame.Surface((size, self.height))
        self.image.fill(pygame.Color(self.color))

    def erase (self):
        ALL_SPRITES[self.layer].remove (self)

class TextSprite (pygame.sprite.Sprite):
    """ Text sprites, can be re-used through set_text """
    def __init__ (self, text, size, color, x=0, y=0, layer=5):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.font = pygame.font.SysFont("Verdana", size)
        self.color = color
        self.image = self.font.render(text, True, color)
        (w, h) = self.font.size (text)
        self.rect = pygame.Rect (x, y, w, h)
        ALL_SPRITES[layer].add (self)

    def set_text (self, text):
        self.image = self.font.render (text, True, self.color)
        (w, h) = self.font.size (text)

    def erase (self):
        ALL_SPRITES[layer].remove (self)


class Display():
    def __init__(self):
        #Initialize Everything
        pygame.init()
        self.screen = pygame.display.set_mode((960, 600))
        pygame.display.set_caption('HexRL')
        #pygame.mouse.set_visible(0)


        #Display The Background
        pygame.display.flip()
        self.key_handlers = defaultdict(list)
        self.mouse_handlers = []
        self.update_handlers = []

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

    def main(self):
        while True:
            for layer in ALL_SPRITES:
                layer.update()
                #Draw Everything
                layer.draw(self.screen)
            pygame.display.flip()
            #Handle Input Events
            for event in pygame.event.get():
                if event.type == QUIT:
                    exit(0)
                elif event.type == KEYDOWN:
                    for handler in self.key_handlers[event.key]:
                        handler(pos)
                elif event.type == MOUSEBUTTONDOWN:
                    for handler in self.mouse_handlers:
                        handler(pos)
                elif event.type == MOUSEMOTION:
                    pass
                elif event.type == MOUSEBUTTONUP:
                    pass
            pos = pygame.mouse.get_pos()
            for handler in self.update_handlers:
                handler(pos)
            time.sleep(0.05)

class Interface ():
    def __init__(self, father, display, ui_sprite_name, keys=[]):
        self.display = display
        self.father = father
        self.keys = keys
        self.ui_sprite_name = ui_sprite_name
        self.ui_sprite = SimpleSprite(ui_sprite_name, layer=1)
        if self.father:
            self.father.desactivate()
        self.activate()

    def desactivate(self):
        self.display.unsubscribe_click(self.on_click)
        self.display.unsubscribe_update(self.update)
        for k, v in self.keys:
            self.display.unsubscribe_key(k, v)
        self.ui_sprite.erase()

    def activate(self):
        self.display.subscribe_click(self.on_click)
        self.display.subscribe_update(self.update)
        for k, v in self.keys:
            self.display.subscribe_key(k, v)
        self.ui_sprite = SimpleSprite(self.ui_sprite_name, layer=1)

    def update(self, pos):
        pass

    def on_click(self, pos):
        pass

    def done(self):
        self.desactivate()
        if self.father:
            self.father.activate()
        else:
            exit(0)

