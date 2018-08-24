from combat import CombatInterface
from display import Interface, TextSprite, SimpleSprite, CascadeElement
from creatures import Creature
from pygame.locals import *
import choices
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
        self.bg.rect.x, self.bg.rect.y = 262, 200
        self.text = TextSprite('Apply to adventurer with [1-5]. [Esc] to cancel.', '#ffffff', 274, 250, maxlen=350)
        self.stats = TextSprite(str(item), '#ffffff', 274, 220, maxlen=350)
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
        try:
            wi.load_game(int(slot))
        except FileNotFoundError as e:
            wi.new_game(int(slot))
        wi.activate()
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
        if not self.teammates:
            for i, pc in enumerate(self.worldinterface.pc_list):
                self.teammates.append(TeammateDisplay(pc, 20, 158 + 40 * i))
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

    def on_step(self, worldinterface):
        pass

    def dict_dump(self):
        return ["MapTile"]

    @staticmethod
    def load(tile, *args):
        return MapTile(tile)

    @staticmethod
    def from_list(d, tile):
        classname = d[0]
        args = d[1:]
        return TILES[classname].load(tile, *args)


class FightTile(MapTile):
    def __init__(self, tile):
        MapTile.__init__(self, tile, 'tiles/GreyTile.png')
        CascadeElement.__init__(self)
        if random.random() > 0.5:
            self.type = 'Skeleton'
            self.fight_sprite = SimpleSprite('tiles/Skeleton.png')
        else:
            self.type = 'Gobelin'
            self.fight_sprite = SimpleSprite('tiles/Gobelin.png')
        self.fight_sprite.rect = self.rect

    def on_step(self, worldinterface):
        if self.type == 'Skeleton':
            min_i = min(4, worldinterface.level // 2 + 1)
            mobs = [('Skeleton', (i, -5 + 0.5 * (i % 2))) for i in range(-min_i, +min_i)]
        elif self.type == 'Gobelin':
            min_i = min(4, worldinterface.level // 2 + 1)
            mobs = [('Gobelin', (i, -5 + 0.5 * (i % 2))) for i in range(-min_i, +min_i)]
        worldinterface.start_combat(mobs=mobs)
        worldinterface.map.board[worldinterface.pc_position] = MapTile(worldinterface.pc_position)

    def dict_dump(self):
        return ["FightTile", self.type]

    def display(self):
        MapTile.display(self)
        self.fight_sprite.display()

    @staticmethod
    def load(tile, *args):
        f = FightTile(tile)
        f.mobs = args[0]
        return f


class GoldTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'icons/gold.png')

    @staticmethod
    def exp_random():
        i = 1
        while random.random() > 0.5:
            i *= 2
        return i

    def on_step(self, worldinterface):
        gold_max = self.exp_random() * worldinterface.level * 2
        gold_min = worldinterface.level
        worldinterface.party_gold += random.randint(gold_min, gold_max)
        worldinterface.map.board[worldinterface.pc_position] = MapTile(worldinterface.pc_position)

    def dict_dump(self):
        return ["GoldTile"]

    @staticmethod
    def load(tile, *args):
        return GoldTile(tile)


class WallTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'tiles/GreyTile2.png')
        self.is_wall = True

    def dict_dump(self):
        return ["WallTile"]

    @staticmethod
    def load(tile, *args):
        return WallTile(tile)


class StairTile(MapTile):
    def __init__(self, tile):
        super().__init__(tile, 'icons/stairs-icon.png')

    def on_step(self, worldinterface):
        worldinterface.map.gen_random()
        worldinterface.pc_position = GameTile(0, 0)
        worldinterface.pc_sprite.rect.x, worldinterface.pc_sprite.rect.y = worldinterface.pc_position.display_location()
        worldinterface.level += 1
        worldinterface.save_game()

    def dict_dump(self):
        return ["StairTile"]

    @staticmethod
    def load(tile, *args):
        return StairTile(tile)


class WorldMap(CascadeElement):
    def __init__(self):
        super().__init__()
        self.board = {}

    def rand_tile(self, game_tile):
        if random.random() > 0.2:
            return MapTile(game_tile)
        if random.random() > 0.5:
            return GoldTile(game_tile)
        return FightTile(game_tile)

    def gen_room(self, tile):
        self.board[tile] = self.rand_tile(tile)
        for neighb in tile.neighbours():
            self.board[neighb] = self.rand_tile(neighb)
            for wall in neighb.neighbours():
                if wall not in self.board:
                    self.board[wall] = WallTile(wall)

    def gen_random(self):
        self.board = {}
        self.gen_room(GameTile(0, 0))
        for neighb in GameTile(0, 0).neighbours():
            self.board[neighb + neighb] = self.rand_tile(neighb + neighb)
            self.gen_room(neighb + neighb + neighb + neighb)
        random_tile = random.choice(list(self.board.keys()))
        self.board[random_tile] = StairTile(random_tile)
        self.board[GameTile(0, 0)] = MapTile(GameTile(0, 0))

    def update(self, pc_position):
        self.subsprites = [t for k, t in self.board.items() if k == pc_position or k in pc_position.raycast(k, valid_steps=[step for step, tile in self.board.items() if not tile.is_wall])]

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
    "FightTile": FightTile,
    "GoldTile": GoldTile,
    "WallTile": WallTile,
    "StairTile": StairTile
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
        #self.current_text = TextSprite('', '#ffffff', 320, 220, maxlen=300)
        #self.choice_text = [TextSprite('', '#ffffff', 320, 400 + 16 * i) for i in range(4)]
        self.pc_position = GameTile(0, 0)
        self.pc_sprite = SimpleSprite('tiles/Fighter.png')
        self.map = WorldMap()
        self.pc_sprite.rect.x, self.pc_sprite.rect.y = self.pc_position.display_location()
        self.subsprites = [self.bg, self.inventory_display, self.map, self.pc_sprite, self.cursor]
        self.formation = [ (-2, 4), (-1, 4.5), (0, 4), (1, 4.5), (2, 4), ]
        Interface.__init__(self, father, keys = [
            ('[4-9]', self.move),
            (K_ESCAPE, self.quit),
            ])

    def on_return(self, defunct=None):
        self.pc_list = [pc for pc in self.pc_list if pc.health > 0]
        self.save_game()

    def on_click(self, mouse_pos):
        self.inventory_display.on_click(mouse_pos)

    def new_game(self, slot):
        self.slot = slot
        self.party_gold = 0
        self.level = 1
        self.pc_list = [
            Creature('Fighter', is_pc=True),
            Creature('Barbarian', is_pc=True),
            Creature('Archer', is_pc=True),
            Creature('Wizard', is_pc=True),
            Creature('Enchantress', is_pc=True),
        ]
        self.map.gen_random()

    def display_choices(self):
        pass

    def move(self, key):
        index = int(key) - 4
        new_position = self.pc_position.neighbours()[index]
        if self.map.board[new_position].is_wall:
            return
        self.pc_position = new_position
        self.pc_sprite.rect.x, self.pc_sprite.rect.y = self.pc_position.display_location()
        self.map.board[self.pc_position].on_step(self)

    def update(self, mouse_pos):
        self.inventory_display.update(mouse_pos)
        self.map.update(self.pc_position)
        self.cursor.rect.x, self.cursor.rect.y = mouse_pos
        self.map.update(self.pc_position)
        self.display()

    def start_combat(self, mobs):
        gi = CombatInterface(self, mobs)
        gi.activate()
        self.desactivate()

    def save_game(self):
        pc_dump = [pc.dict_dump()for pc in self.pc_list]
        inventory_dump = [item.name for item in self.inventory]
        save = {
                'pcs':pc_dump, 
                'gold':self.party_gold,
                'level': self.level,
                'map':self.map.dict_dump(),
                'inventory_dump': inventory_dump
                }
        with open('save%d.json' % self.slot, 'w') as f:
            f.write(json.dumps(save))

    def quit(self, mouse_pos):
        self.done()

    def erase_save(self):
        os.unlink('save%d.json' % self.slot)

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
        self.map.load_dict(d['map'])
        self.display_choices()

    def pay(self, amount):
        self.party_gold -= amount

