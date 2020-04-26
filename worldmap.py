from combat import CombatInterface
from display import Interface, TextSprite, SimpleSprite, CascadeElement
from creatures import Creature
from pygame.locals import *
import random
import items
import json
import os
from gametile import GameTile

class EquipInterface(Interface, CascadeElement):
    def __init__(self, father, item):
        CascadeElement.__init__(self)
        self.item = item
        self.bg = SimpleSprite('helpmodal.png')
        self.bg.rect.x, self.bg.rect.y = 302, 200
        self.text = TextSprite('Apply to adventurer with [1-5]. [Esc] to cancel.', '#ffffff', 330, 250, maxlen=350)
        self.stats = TextSprite(str(item), '#ffffff', 330, 220, maxlen=350)
        self.subsprites = [self.bg, self.stats, self.text]
        Interface.__init__(self, father, keys=[
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


class GameOverModal(Interface, CascadeElement):
    def __init__(self, father):
        CascadeElement.__init__(self)
        Interface.__init__(self, father, keys=[
            (K_ESCAPE, self.cancel),
            (K_RETURN, self.cancel)
        ])
        self.basex, self.basey = 302, 200
        self.bg = SimpleSprite('helpmodal.png')
        self.bg.rect.move_ip(self.basex, self.basey)
        self.text = TextSprite('Your party is dead. Game Over.', '#ffffff', 330, 250, maxlen=350)
        self.subsprites = [self.bg, self.text]
        self.display()

    def cancel(self, key):
        self.done()
        self.father.done()


class MainMenuInterface(Interface, CascadeElement):
    def __init__(self):
        CascadeElement.__init__(self)
        self.bg = SimpleSprite('menu.png')
        self.hello = TextSprite('Choose a save slot with keys 1-3', '#ffffff', 320, 280)
        self.slots = []
        for i in range(3):
            try:
                slotname = 'Day %d' % json.load(open('save%d.json' % (i + 1)))['level']
            except FileNotFoundError:
                slotname = 'Empty'
            self.slots.append(TextSprite('[%d] Slot - %s' % (i + 1, slotname), '#ffffff', 320, 300 + 20 * i))
        self.subsprites = [self.bg, self.hello] + self.slots
        Interface.__init__(self, None, keys=[
            (K_ESCAPE, lambda x: self.done()),
            ('[1-3]', self.start),
        ])

    def start(self, slot):
        wi = WorldInterface(self)
        wi.activate()
        try:
            wi.load_game(int(slot))
        except FileNotFoundError as e:
            wi.new_game(int(slot))
        wi.display()
        self.desactivate()

    def on_return(self, defunct=None):
        for i in range(3):
            try:
                slotname = 'Level %d' % json.load(open('save%d.json' % (i + 1)))['level']
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
        self.food_icon = SimpleSprite('icons/apple.png')
        self.food_icon.rect.x, self.food_icon.rect.y = 92, 50
        self.food_stat = TextSprite('', '#ffffff', 130, 54)
        self.day_text = TextSprite('', '#ffffff', 20, 90)
        self.inventory = []
        self.items = []
        for i in range(10):
            self.inventory.append(SimpleSprite('icons/icon-blank.png'))
            self.inventory[i].rect.x, self.inventory[i].rect.y = 50 + (i % 5) * 32, 380 + (i // 5) * 32
        self.subsprites = [self.gold_icon, self.gold_stat, self.food_icon, self.food_stat,
                           self.day_text] + self.inventory
        self.teammates = []

    def update(self, mouse_pos):
        if not self.teammates:
            for i, pc in enumerate(self.worldinterface.pc_list):
                self.teammates.append(TeammateDisplay(pc, 20, 158 + 40 * i))
        self.gold_stat.set_text(str(self.worldinterface.party_gold))
        self.food_stat.set_text(str(self.worldinterface.party_food))
        self.day_text.set_text("Level %d" % self.worldinterface.level)

        for pc in self.teammates:
            pc.update()

        for i, item in enumerate(self.worldinterface.inventory):
            item.rect.x, item.rect.y = self.inventory[i].rect.x, self.inventory[i].rect.y
            self.items.append(item)
        for item in self.items.copy():
            if item not in self.worldinterface.inventory:
                self.items.remove(item)
        self.subsprites = [self.gold_icon, self.gold_stat, self.day_text, self.food_icon,
                           self.food_stat] + self.inventory + self.teammates + self.items

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

class ShopModal(Interface, CascadeElement):
    def __init__(self, father):
        CascadeElement.__init__(self)
        self.bg = SimpleSprite('helpmodal.png')
        self.bg.rect.x, self.bg.rect.y = 302, 200
        self.text = TextSprite('Items to buy. [Esc] to leave.', '#ffffff', 330, 250)
        self.items = []
        self.item_texts = []
        father.desactivate()
        for i in range(3):
            choice = random.choice(list(items.ITEMS.keys()))
            item_class = items.ITEMS[choice][0]
            item_args = items.ITEMS[choice][1]
            item = item_class(*item_args)
            self.items.append(item)
            self.item_texts.append(
                TextSprite("[%d]: %s - %d gold" % (i + 1, item.name, item.shop_price), "#ffffff", 368, 304 + 40 * i))

        Interface.__init__(self, father, keys=[
            (K_ESCAPE, self.leave),
            ('[1-3]', self.buy),
        ])

    def buy(self, code):
        num = int(code) - 1
        if num >= len(self.items):
            return
        if self.father.party_gold < self.items[num].shop_price:
            return
        self.father.party_gold -= self.items[num].shop_price
        self.father.inventory.append(self.items[num])
        self.items.pop(num)
        self.item_texts.pop(num)

    def leave(self, _):
        self.done()

    def update(self, mouse_pos):
        for i, item in enumerate(self.items):
            item.rect.x, item.rect.y = 330, 300 + 40 * i
            self.item_texts[i] = TextSprite("[%d]: %s - %d gold" % (i + 1, item.name, item.shop_price), "#ffffff", 368,
                                            304 + 40 * i)
        self.subsprites = [self.bg, self.text] + self.items + self.item_texts
        self.father.update(mouse_pos)
        self.display()


class WorldInterface(Interface, CascadeElement):
    def __init__(self, father):
        CascadeElement.__init__(self)
        self.inventory_display = StatusDisplay(self)
        self.mob_list = []
        self.bg = SimpleSprite('menu.png')
        self.inventory = []
        self.cursor = SimpleSprite('icons/magnifyingglass.png')
        self.pc_position = GameTile(0, 0)
        self.pc_sprite = SimpleSprite('tiles/Fighter.png')
        self.subsprites = [self.bg, self.inventory_display, self.pc_sprite, self.cursor]
        self.wave = 1
        self.formation = [(-2, 4), (-1, 4.5), (0, 4), (1, 4.5), (2, 4), ]
        Interface.__init__(self, father)

    def on_return(self, defunct=None):
        self.pc_list = [pc for pc in self.pc_list if pc.health > 0]
        if not self.pc_list:
            self.erase_save()
            game_over = GameOverModal(self)
            self.desactivate()
            game_over.activate()
        if isinstance(defunct, ShopModal):
            self.start_combat(['Gobelin'])
        else:
            self.party_gold += self.level * 10
            self.level += 1
            self.shop = ShopModal(self)
            self.shop.activate()

    def on_click(self, mouse_pos):
        self.inventory_display.on_click(mouse_pos)

    def new_game(self, slot):
        self.slot = slot
        self.party_gold = 0
        self.party_food = 400
        self.level = 1
        self.pc_list = [
            Creature('Fighter', is_pc=True),
            Creature('Barbarian', is_pc=True),
            Creature('Archer', is_pc=True),
            Creature('Wizard', is_pc=True),
            Creature('Enchantress', is_pc=True),
        ]
        self.shop = ShopModal(self)
        self.shop.activate()

    def display_choices(self):
        pass

    def update(self, mouse_pos):
        self.inventory_display.update(mouse_pos)
        self.pc_sprite.rect.x, self.pc_sprite.rect.y = self.pc_position.display_location()
        self.cursor.rect.x, self.cursor.rect.y = mouse_pos
        self.display()

    def start_combat(self, mobs):
        self.save_game()
        gi = CombatInterface(self, mobs)
        gi.activate()
        self.desactivate()

    def save_game(self):
        pc_dump = [pc.dict_dump() for pc in self.pc_list]
        inventory_dump = [item.name for item in self.inventory]
        save = {
            'pcs': pc_dump,
            'gold': self.party_gold,
            'food': self.party_food,
            'level': self.level,
            'inventory_dump': inventory_dump,
            'pc_position': self.pc_position.dict_dump()
        }
        with open('save%d.json' % self.slot, 'w') as f:
            f.write(json.dumps(save))

    def quit(self, mouse_pos):
        self.save_game()
        self.done()

    def erase_save(self):
        try:
            os.unlink('save%d.json' % self.slot)
        except FileNotFoundError:
            pass

    def load_game(self, slot):
        self.slot = slot
        with open('save%d.json' % slot) as f:
            d = json.loads(f.read())
        self.party_gold = d['gold']
        self.pc_position = GameTile.from_string(d['pc_position'])
        self.level = d['level']
        self.party_food = d['food']
        for key in d['inventory_dump']:
            item_class = items.ITEMS[key][0]
            item_args = items.ITEMS[key][1]
            self.inventory.append(item_class(*item_args))
        self.pc_list = [Creature.dict_load(pc, self.inventory) for pc in d['pcs']]

    def pay(self, amount):
        self.party_gold -= amount
