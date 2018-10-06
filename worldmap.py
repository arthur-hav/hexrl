from combat import CombatInterface
from display import Interface, TextSprite, SimpleSprite, CascadeElement
from creatures import Creature
from pygame.locals import *
import random
import items
import json
import os
from gametile import GameTile
import math


class EquipInterface(Interface, CascadeElement):
    def __init__(self, father, item):
        CascadeElement.__init__(self)
        self.item = item
        self.bg = SimpleSprite('helpmodal.png')
        self.bg.rect.x, self.bg.rect.y = 302, 200
        self.text = TextSprite('Apply to adventurer with [1-5]. [Esc] to cancel.', '#ffffff', 330, 250, maxlen=350)
        self.stats = TextSprite(str(item), '#ffffff', 330, 220, maxlen=350)
        self.subsprites = [self.bg, self.stats, self.text]
        Interface.__init__(self, father, keys = [
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
        Interface.__init__(self,father, keys = [
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
        Interface.__init__(self, None, keys = [
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
        self.subsprites = [self.gold_icon, self.gold_stat, self.food_icon, self.food_stat, self.day_text] + self.inventory
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
        self.subsprites = [self.gold_icon, self.gold_stat, self.day_text, self.food_icon, self.food_stat] + self.inventory + self.teammates + self.items

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


class MapTile(SimpleSprite):
    def __init__(self, tile, image_name='tiles/GreyTile.png'):
        super().__init__(image_name)
        self.rect.move_ip(*tile.display_location())
        self.is_wall = False

    def on_step(self, world_interface):
        pass

    def dict_dump(self):
        return self.__class__.__name__

    @staticmethod
    def from_list(classname, tile):
        return TILES[classname](tile)


class SkeletonTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'tiles/GreyTile.png')
        self.fight_sprite = SimpleSprite('tiles/Skeleton.png')
        self.fight_sprite.rect = self.rect

    def on_step(self, world_interface):
        num_skeletons = 2 + min(6, world_interface.level // 2)
        num_archers = min(5, world_interface.level // 3)
        num_necro = min(2, world_interface.level//11)

        mobs = ['Skeleton'] * num_skeletons + ['SkeletonArcher'] * num_archers + ['Necromancer'] * num_necro
        world_interface.start_combat(mobs=mobs)
        world_interface.party_gold += random.randint(5 + world_interface.level // 2, 10 + world_interface.level * 2)
        world_interface.map.board[world_interface.pc_position] = MapTile(world_interface.pc_position)

    def display(self):
        MapTile.display(self)
        self.fight_sprite.display()


class GobelinTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'tiles/GreyTile.png')
        self.fight_sprite = SimpleSprite('tiles/Gobelin.png')
        self.fight_sprite.rect = self.rect

    def on_step(self, world_interface):
        num_gobelins = 1 + min(6, world_interface.level // 2)
        num_trolls = min(5, world_interface.level // 3)
        mobs = ['Gobelin'] * num_gobelins + ['Troll'] * num_trolls
        world_interface.start_combat(mobs=mobs)
        world_interface.party_gold += random.randint(4 + world_interface.level // 2, 8 + world_interface.level * 2)
        world_interface.party_food += random.randint(40, 100)
        world_interface.map.board[world_interface.pc_position] = MapTile(world_interface.pc_position)

    def display(self):
        MapTile.display(self)
        self.fight_sprite.display()


class BansheeTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'tiles/GreyTile.png')
        self.fight_sprite = SimpleSprite('tiles/Banshee.png')
        self.fight_sprite.rect = self.rect

    def on_step(self, world_interface):
        num_banshees = 2 + min(6, world_interface.level // 3)
        mobs = ['Banshee'] * num_banshees
        world_interface.start_combat(mobs=mobs)
        world_interface.party_gold += random.randint(5 + world_interface.level, 10 + world_interface.level * 4)
        world_interface.map.board[world_interface.pc_position] = MapTile(world_interface.pc_position)

    def display(self):
        MapTile.display(self)
        self.fight_sprite.display()


class DemonTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'tiles/GreyTile.png')
        self.fight_sprite = SimpleSprite('tiles/Demon.png')
        self.fight_sprite.rect = self.rect

    def on_step(self, world_interface):
        num_demons = min(2, world_interface.level // 10)
        num_imp = min(12, random.randint(0, world_interface.level // 2))
        mobs = ['Demon'] * num_demons + ['Imp'] * num_imp
        world_interface.start_combat(mobs=mobs)
        world_interface.party_gold += random.randint(5 + world_interface.level, 10 + world_interface.level * 4)
        world_interface.map.board[world_interface.pc_position] = MapTile(world_interface.pc_position)

    def display(self):
        MapTile.display(self)
        self.fight_sprite.display()


class GoldTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'tiles/gold.png')

    def on_step(self, world_interface):
        world_interface.party_gold += random.randint(5 + world_interface.level, 10 + world_interface.level * 3)
        world_interface.map.board[world_interface.pc_position] = MapTile(world_interface.pc_position)


class FoodTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'tiles/apple.png')

    def on_step(self, world_interface):
        world_interface.party_food += random.randint(40, 160)
        world_interface.map.board[world_interface.pc_position] = MapTile(world_interface.pc_position)


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
            choice = random.choice( list(items.ITEMS.keys()) )
            item_class = items.ITEMS[choice][0]
            item_args = items.ITEMS[choice][1]
            item = item_class(*item_args)
            self.items.append(item)
            self.item_texts.append(TextSprite("[%d]: %s - %d gold" % (i + 1, item.name, item.shop_price), "#ffffff", 368, 304 + 40 * i))

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
            self.item_texts[i] = TextSprite("[%d]: %s - %d gold" % (i + 1, item.name, item.shop_price), "#ffffff", 368, 304 + 40 * i)
        self.subsprites = [self.bg, self.text] + self.items + self.item_texts
        self.father.update(mouse_pos)
        self.display()


class ShopTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, image_name='tiles/Shop.png')

    def on_step(self, world_interface):
        sm = ShopModal(world_interface)
        sm.activate()
        world_interface.map.board[world_interface.pc_position] = MapTile(world_interface.pc_position)


class WallTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'tiles/GreyTile2.png')
        self.is_wall = True


class StairTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'icons/stairs-icon.png')

    def on_step(self, world_interface):
        world_interface.pc_position = world_interface.map.gen_random()
        world_interface.pc_sprite.rect.x, world_interface.pc_sprite.rect.y = world_interface.pc_position.display_location()
        for cr in world_interface.pc_list:
            cr.health += math.ceil((cr.maxhealth - cr.health) * 25 / 100)
        world_interface.map.seen = set()
        world_interface.level += 1


def rand_tile(game_tile, level):
    empty_ratio = 0.5 + 0.4 / level
    if random.random() < 0.02:
        return ShopTile(game_tile)
    if random.random() < 0.05:
        return GoldTile(game_tile)
    if random.random() < 0.05:
        return FoodTile(game_tile)
    if random.random() < empty_ratio:
        return MapTile(game_tile)
    demon_ratio = min(0.25, (level - 10) / 10)
    if random.random() < demon_ratio:
        return DemonTile(game_tile)
    banshee_ratio = min(0.3, (level - 5) / 5)
    if random.random() < banshee_ratio:
        return BansheeTile(game_tile)
    if random.random() < 0.5:
        return SkeletonTile(game_tile)
    return GobelinTile(game_tile)


class WorldMap(CascadeElement):
    def __init__(self, level):
        super().__init__()
        self.board = {}
        self.seen = set()
        self.level = level

    def gen_room(self, tile):
        self.board[tile] = WallTile(tile)
        for neighb in tile.neighbours():
            self.board[neighb] = rand_tile(neighb, self.level)
            for wall in neighb.neighbours():
                if wall not in self.board:
                    self.board[wall] = WallTile(wall)

    def gen_random(self):
        self.board = {}
        self.gen_room(GameTile(0, 0))
        extremums = []
        for neighb in GameTile(0, 0).neighbours():
            self.board[neighb + neighb] = rand_tile(neighb + neighb, self.level)
            self.gen_room(neighb + neighb + neighb + neighb)
            extremums.append(neighb+neighb+neighb+neighb+neighb+neighb)
        random_stair = random.choice(extremums)
        extremums.remove(random_stair)
        self.board[random_stair] = StairTile(random_stair)
        pc_tile = random.choice(extremums)
        pc_tile = GameTile(pc_tile.x * 5 / 6, pc_tile.y * 5 / 6)
        self.board[pc_tile] = MapTile(pc_tile)
        return pc_tile

    def update(self, pc_position):
        valid_steps = [step for step, tile in self.board.items() if not tile.is_wall]
        seen_tiles = [k for k, t in self.board.items() if k.dist(pc_position) < 3.25 and (k == pc_position or
                            k in pc_position.raycast(k, valid_steps=valid_steps))]
        self.seen |= set(seen_tiles)
        self.subsprites = [self.board[k] for k in self.seen]

    def dict_dump(self):
        d = {}
        for k, v in self.board.items():
            d[k.dict_dump()] = v.dict_dump()
        return d

    def load_dict(self, d):
        for k, v in d.items():
            tile = GameTile.from_string(k)
            self.board[tile] = MapTile.from_list(v, tile)

TILES = {
    "MapTile": MapTile,
    "GoldTile": GoldTile,
    "WallTile": WallTile,
    "StairTile": StairTile,
    "SkeletonTile": SkeletonTile,
    "GobelinTile": GobelinTile,
    "DemonTile": DemonTile,
    "BansheeTile": BansheeTile,
    "ShopTile": ShopTile,
    "FoodTile": FoodTile
}


class WorldInterface(Interface, CascadeElement):
    def __init__(self, father):
        CascadeElement.__init__(self)
        self.inventory_display = StatusDisplay(self)
        self.mob_list = []
        self.current_question_key = ''
        self.previous_question = ''
        self.current_question = None
        self.bg = SimpleSprite('menu.png')
        self.inventory = []
        self.cursor = SimpleSprite('icons/magnifyingglass.png')
        self.pc_position = GameTile(0, 0)
        self.pc_sprite = SimpleSprite('tiles/Fighter.png')
        self.map = WorldMap(0)
        self.subsprites = [self.bg, self.inventory_display, self.map, self.pc_sprite, self.cursor]
        self.formation = [ (-2, 4), (-1, 4.5), (0, 4), (1, 4.5), (2, 4), ]
        Interface.__init__(self, father, keys=[
            ('[4-9]', self.move),
            (K_ESCAPE, self.quit),
            ])

    def on_return(self, defunct=None):
        self.pc_list = [pc for pc in self.pc_list if pc.health > 0]
        if not self.pc_list:
            self.erase_save()
            game_over = GameOverModal(self)
            self.desactivate()
            game_over.activate()

    def on_click(self, mouse_pos):
        self.inventory_display.on_click(mouse_pos)

    def new_game(self, slot):
        self.slot = slot
        self.party_gold = 0
        self.party_food = 400
        self.level = 1
        self.map.level = 1
        self.pc_list = [
            Creature('Fighter', is_pc=True),
            Creature('Barbarian', is_pc=True),
            Creature('Archer', is_pc=True),
            Creature('Wizard', is_pc=True),
            Creature('Enchantress', is_pc=True),
        ]
        self.pc_position = self.map.gen_random()

    def display_choices(self):
        pass

    def move(self, key):
        index = int(key) - 4
        new_position = self.pc_position.neighbours()[index]
        if self.map.board[new_position].is_wall:
            return
        self.party_food -= len(self.pc_list)
        if self.party_food < 0:
            self.erase_save()
            game_over = GameOverModal(self)
            self.desactivate()
            game_over.activate()
        self.pc_position = new_position
        self.map.board[self.pc_position].on_step(self)

    def update(self, mouse_pos):
        self.inventory_display.update(mouse_pos)
        self.pc_sprite.rect.x, self.pc_sprite.rect.y = self.pc_position.display_location()
        self.map.update(self.pc_position)
        self.cursor.rect.x, self.cursor.rect.y = mouse_pos
        self.map.update(self.pc_position)
        self.display()

    def start_combat(self, mobs):
        self.save_game()
        gi = CombatInterface(self, mobs)
        gi.activate()
        self.desactivate()

    def save_game(self):
        pc_dump = [pc.dict_dump()for pc in self.pc_list]
        inventory_dump = [item.name for item in self.inventory]
        save = {
                'pcs':pc_dump, 
                'gold':self.party_gold,
                'food':self.party_food,
                'level': self.level,
                'map':self.map.dict_dump(),
                'inventory_dump': inventory_dump,
                'pc_position':self.pc_position.dict_dump()
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
        self.map.level = self.level
        for key in d['inventory_dump']:
            item_class = items.ITEMS[key][0]
            item_args = items.ITEMS[key][1]
            self.inventory.append(item_class(*item_args))
        self.pc_list = [Creature.dict_load(pc, self.inventory) for pc in d['pcs']]
        self.map.load_dict(d['map'])
        self.map.board[self.pc_position].on_step(self)

    def pay(self, amount):
        self.party_gold -= amount

