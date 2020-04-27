from combat import CombatInterface
from display import Interface, TextSprite, SimpleSprite, CascadeElement, Gauge
from creatures import Creature
from pygame.locals import *
import random
import items
import json
import os

class FightButton(CascadeElement):
    def __init__(self):
        CascadeElement.__init__(self)
        self.text = TextSprite('FIGHT', '#ffffff', 480, 480)
        txt = self.text.textsprites[0]
        self.bg = Gauge(txt.rect.w * 2 + 4, txt.rect.h * 2 + 4, "#ff0000")
        self.bg.move_to(txt.rect.x - 2, txt.rect.y - 2)
        self.subsprites = [self.bg, self.text]

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
        self.day_text = TextSprite('', '#ffffff', 20, 90)
        self.inventory = []
        self.items = []
        for i in range(10):
            self.inventory.append(SimpleSprite('icons/icon-blank.png'))
            self.inventory[i].rect.x, self.inventory[i].rect.y = 50 + (i % 5) * 32, 380 + (i // 5) * 32
        self.subsprites = [self.gold_icon, self.gold_stat, self.day_text] + self.inventory
        self.teammates = []

    def update(self, mouse_pos):
        self.teammates = [TeammateDisplay(pc, 20, 158 + 40 * i) for i, pc in enumerate(self.worldinterface.pc_list)]
        self.gold_stat.set_text(str(self.worldinterface.party_gold))
        self.day_text.set_text("Level %d" % self.worldinterface.level)

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

        for pc in self.worldinterface.pc_list:
            for item in pc.items:
                if item.rect.collidepoint(mouse_pos):
                    item.unequip()
                    self.worldinterface.inventory.append(item)

class Shop(CascadeElement):
    def __init__(self, father):
        CascadeElement.__init__(self)
        self.items = []
        self.item_texts = []
        self.father = father
        self.init_shop()

    def init_shop(self):
        self.items = []
        self.item_texts = []
        self.mercenary = Creature(random.choice(['Barbarian', 'Fighter', 'Archer', 'Wizard', 'Enchantress']), is_pc=True)
        self.mercenary.rect.x, self.mercenary.rect.y = 330, 150
        self.mercenary_price = 400 + len(self.father.pc_list) ** 2 * 50
        self.item_texts.append(TextSprite(f"Mercenary {self.mercenary.name} - {self.mercenary_price} gold", "#ffffff", 368, 154))

        for i in range(5):
            choice = random.choice(list(items.ITEMS.keys()))
            item_class = items.ITEMS[choice][0]
            item_args = items.ITEMS[choice][1]
            item = item_class(*item_args)
            self.items.append(item)
            self.item_texts.append(
                TextSprite("%s - %d gold" % (item.name, item.shop_price), "#ffffff", 368, 154 + 40 * i))

    def buy(self, item):
        num = self.items.index(item)
        if self.father.party_gold < self.items[num].shop_price:
            return
        self.father.party_gold -= self.items[num].shop_price
        self.father.inventory.append(self.items[num])
        self.items.pop(num)
        self.item_texts.pop(num)

    def buy_merc(self):
        if self.father.party_gold < self.mercenary_price:
            return
        self.father.party_gold -= self.mercenary_price
        self.father.pc_list.append(self.mercenary)
        self.item_texts[0].set_text("")
        self.mercenary = None

    def update(self, mouse_pos):

        for i, item in enumerate(self.items, 1):
            item.rect.x, item.rect.y = 330, 150 + 40 * i
            self.item_texts[i] = TextSprite("%s - %d gold" % (item.name, item.shop_price), "#ffffff", 368,
                                            154 + 40 * i)
        self.subsprites = ([self.mercenary] if self.mercenary else []) + self.items + self.item_texts
        self.display()

    def on_click(self, mouse_pos):
        for item in self.items:
            if item.rect.collidepoint(mouse_pos):
                self.buy(item)
        if self.mercenary and self.mercenary.rect.collidepoint(mouse_pos):
            self.buy_merc()


class WorldInterface(Interface, CascadeElement):
    def __init__(self, father):
        CascadeElement.__init__(self)
        self.inventory_display = StatusDisplay(self)
        self.mob_list = []
        self.bg = SimpleSprite('menu.png')
        self.inventory = []
        self.dragged_item = None
        self.cursor = SimpleSprite('icons/magnifyingglass.png')
        self.fight_button = FightButton()
        self.tooltip = TextSprite("", "#ffffff", 20, 480, maxlen=200)
        self.subsprites = [self.bg, self.fight_button, self.inventory_display, self.cursor, self.tooltip]
        self.formation = [(-2, 4), (-1, 4.5), (0, 4), (1, 4.5), (2, 4), ]
        self.pc_list = [
            Creature(random.choice(['Barbarian', 'Fighter', 'Archer', 'Wizard', 'Enchantress']), is_pc=True)
        ]
        self.shop = Shop(self)
        Interface.__init__(self, father,
                           keys=[(K_ESCAPE, self.quit)])

    def on_return(self, defunct=None):
        self.pc_list = [pc for pc in self.pc_list if pc.health > 0]
        if not self.pc_list:
            self.erase_save()
            game_over = GameOverModal(self)
            self.desactivate()
            game_over.activate()
        self.level += 1
        self.party_gold += 50 + 10 * self.level
        self.shop.init_shop()

    def on_click(self, mouse_pos):
        self.inventory_display.on_click(mouse_pos)
        self.shop.on_click(mouse_pos)
        if self.fight_button.bg.rect.collidepoint(mouse_pos):
            self.start_combat(['Gobelin'])
        for item in self.inventory:
            if item.rect.collidepoint(mouse_pos):
                self.dragged_item = item
                self.inventory.remove(item)

    def on_mouseup(self, pos):
        if self.dragged_item:
            for pc in self.pc_list:
                if pc.rect.colliderect(self.cursor.rect):
                    self.dragged_item.equip(pc)
                    self.dragged_item = None
                    return
            self.inventory.append(self.dragged_item)
            self.dragged_item = None

    def new_game(self, slot):
        self.slot = slot
        self.party_gold = 0
        self.level = 1


    def update(self, mouse_pos):
        self.inventory_display.update(mouse_pos)
        if self.dragged_item:
            self.cursor = self.dragged_item
        else:
            self.cursor = SimpleSprite('icons/magnifyingglass.png')
        self.cursor.rect.x, self.cursor.rect.y = mouse_pos
        self.subsprites[4] = self.cursor
        self.display()
        self.tooltip.set_text("")
        for item in self.inventory:
            if item.rect.collidepoint(mouse_pos):
                self.tooltip.set_text(str(item))
        for item in self.shop.items:
            if item.rect.collidepoint(mouse_pos):
                self.tooltip.set_text(str(item))
        self.shop.update(mouse_pos)

    def save_game(self):
        pc_dump = [pc.dict_dump() for pc in self.pc_list]
        inventory_dump = [item.name for item in self.inventory]
        save = {
            'pcs': pc_dump,
            'gold': self.party_gold,
            'level': self.level,
            'inventory_dump': inventory_dump,
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
        self.level = d['level']
        for key in d['inventory_dump']:
            item_class = items.ITEMS[key][0]
            item_args = items.ITEMS[key][1]
            self.inventory.append(item_class(*item_args))
        self.pc_list = [Creature.dict_load(pc, self.inventory) for pc in d['pcs']]
        self.shop = Shop(self)

    def pay(self, amount):
        self.party_gold -= amount

    def combat(self, _):
        self.start_combat(['Gobelin'])

    def start_combat(self, mobs):
        self.save_game()
        gi = CombatInterface(self, mobs, self.pc_list, self.formation)
        gi.activate()
        self.desactivate()
