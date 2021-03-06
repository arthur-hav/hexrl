from display import *
from math import ceil
from pygame.locals import *
from gametile import GameTile


def dfs(creature, tile, maxdepth, radius, visited=None):
    if not visited:
        visited = {tile}
    if maxdepth == 0:
        return visited
    for neighb in tile.neighbours():
        if neighb.in_boundaries(radius) and (neighb not in creature.combat.creatures or creature.combat.creatures[neighb].is_pc):
            visited.add(neighb)
            dfs(creature, neighb, maxdepth - 1, radius, visited)
    return visited


class Arena(CascadeElement):
    def __init__(self, radius):
        super().__init__()
        self.radius = radius
        self.board = {}
        for tile in GameTile.all_tiles(radius):
            self.board[tile] = SimpleSprite('tiles/GreyTile.png')
            self.board[tile].rect.move_ip(*tile.display_location())
        self.subsprites = list(self.board.values())

    def update(self, creature):
        for sprite in self.board.values():
            sprite.animate('tiles/GreyTile.png')
        if creature.is_pc:
            for tile in dfs(creature, creature.tile, creature.free_moves + 1, self.radius):
                self.board[tile].animate('tiles/Green1.png')
        self.board[creature.tile].animate('tiles/Green2.png')


class InfoDisplay (CascadeElement):
    def __init__ (self, basex, basey):
        super().__init__()
        self.portrait = SimpleSprite('portraits/Fighter.png')
        self.portrait.rect.x, self.portrait.rect.y = basex, basey

        self.description = TextSprite('', '#ffffff', basex, basey + 192, maxlen=120)
        self.tooltip = Tooltip()
        self.tooltip.must_show = False
        self.health = SimpleSprite('icons/heart.png')
        self.health.rect.move_ip(basex + 152, basey + 4)
        self.health_stat = TextSprite('', '#ffffff', basex + 188, basey + 8)
        self.damage = SimpleSprite('icons/sword.png')
        self.damage.rect.move_ip(basex + 228, basey + 4)
        self.damage_stat = TextSprite('', '#ffffff', basex + 264, basey + 8)

        self.armor = SimpleSprite('icons/armor.png')
        self.armor.rect.move_ip(basex + 152, basey + 42)
        self.armor_stat = TextSprite('', '#ffffff', basex + 188, basey + 46)
        self.mr = SimpleSprite('icons/magic-resist.png')
        self.mr.rect.move_ip(basex + 228, basey + 42)
        self.mr_stat = TextSprite('', '#ffffff', basex + 264, basey + 46)

        self.status_effect_display = StatusEffectDisplay(basex + 152, basey + 80)
        self.ability_display = AbilityDisplay(basex, basey + 250)
        self.passive_display = PassiveAbilitiesDisplay(basex, basey + 370)
        self.subsprites = [self.portrait, self.health, self.health_stat, self.damage, self.damage_stat, self.armor,
                           self.armor_stat, self.mr, self.mr_stat, self.description, self.status_effect_display,
                           self.ability_display, self.passive_display, self.tooltip]

    def update(self, creature, mouse_pos):
        self.tooltip.must_show = True
        if self.health.rect.collidepoint(mouse_pos):
            self.tooltip.set_text("Health\nA creature is killed if this reaches 0.")
        elif self.damage.rect.collidepoint(mouse_pos):
            self.tooltip.set_text("Damage\nDamage inflicted per melee attack. Also influences ability damage.")
        elif creature.magic_resist and self.mr.rect.collidepoint(mouse_pos):
            self.tooltip.set_text("Magic resist\nDivides magic damage inflicted by 1 + MR/10.")
        elif creature.armor and self.armor.rect.collidepoint(mouse_pos):
            self.tooltip.set_text("Armor\nDivides physical damage inflicted by 1 + ARM/10.")
        else:
            self.tooltip.must_show = False
        self.status_effect_display.update(creature, mouse_pos)
        if not creature:
            return
        self.portrait.animate(creature.portrait)
        self.damage_stat.set_text(str(creature.damage))
        self.health_stat.set_text(str(creature.health))
        self.description.set_text(str(getattr(creature, 'description', '')))
        if creature.magic_resist:
            self.mr_stat.set_text(str(creature.magic_resist))
            self.mr.must_show = True
            self.mr_stat.must_show = True
        else:
            self.mr.must_show = False
            self.mr_stat.must_show = False
        if creature.armor:
            self.armor_stat.set_text(str(creature.armor))
            self.armor.must_show = True
            self.armor_stat.must_show = True
        else:
            self.armor.must_show = False
            self.armor_stat.must_show = False
        self.ability_display.update(creature, mouse_pos)
        self.passive_display.update(creature, mouse_pos)


class AbilityDisplay (CascadeElement):
    def __init__ (self, basex, basey):
        super().__init__()
        self.basex = basex
        self.basey = basey
        self.tooltip = Tooltip()
        self.text = TextSprite('Abilities', '#ffffff', basex, basey)

    def update(self, creature, mouse_pos):
        self.subsprites = [self.text]
        for i, ability in enumerate(creature.abilities):
            xoff, yoff = 152 * (i % 2), 40 * (i // 2)
            if ability.current_cooldown:
                text = '<%d>' % ceil(ability.current_cooldown / 100)
                image = ability.image_cd
            else:
                text = ability.name
                image = ability.image_name
            key_hint = TextSprite("[%d]" % (i + 1), '#ffffff', self.basex + xoff, self.basey + 24 + yoff)
            sprite = SimpleSprite(image)
            sprite.rect.x, sprite.rect.y = (self.basex + 32 + xoff, self.basey + 20 + yoff)
            if sprite.rect.collidepoint(mouse_pos):
                self.tooltip.set_text("%s\n%s" % (ability.name, ability.description))
                if self.tooltip not in self.subsprites:
                    self.subsprites.append(self.tooltip)
            elif self.tooltip in self.subsprites:
                self.subsprites.remove(self.tooltip)
            text_sprite = TextSprite(text, '#ffffff', self.basex + 70 + xoff, self.basey + 24 + yoff)
            self.subsprites.append(sprite)
            self.subsprites.append(key_hint)
            self.subsprites.append(text_sprite)


class StatusEffectDisplay (CascadeElement):
    def __init__ (self, basex, basey):
        super().__init__()
        self.basex = basex
        self.basey = basey
        self.text = TextSprite('Status effects', '#ffffff', self.basex, self.basey)
        self.tooltip = Tooltip()

    def update(self, creature, mouse_pos):
        if not creature.status:
            self.subsprites = []
            return
        self.subsprites = [self.text]
        for i, status in enumerate(creature.status):
            xoff, yoff = 0, 32 * i
            text = '%s <%d>' % (status.name, ceil(creature.status[i].duration / 100))
            text_sprite = TextSprite(text, '#ffffff', self.basex + 38 + xoff, self.basey + 24 + yoff)
            sprite = SimpleSprite(status.image_name)
            sprite.rect.x, sprite.rect.y = (self.basex + xoff, self.basey + 20 + yoff)
            self.subsprites.append(sprite)
            self.subsprites.append(text_sprite)
            if sprite.rect.collidepoint(mouse_pos):
                self.tooltip.set_text("%s\n%s" % (status.name, status.get_description()))
                if self.tooltip not in self.subsprites:
                    self.subsprites.append(self.tooltip)
            elif self.tooltip in self.subsprites:
                self.subsprites.remove(self.tooltip)


class PassiveAbilitiesDisplay (CascadeElement):
    def __init__ (self, basex, basey):
        super().__init__()
        self.basex = basex
        self.basey = basey
        self.text = TextSprite('Passive ability', '#ffffff', self.basex, self.basey)
        self.tooltip = Tooltip()

    def update(self, creature, mouse_pos):
        if not creature.passives:
            self.subsprites = []
            return
        self.subsprites = [self.text]
        for i, passive in enumerate(creature.passives):
            xoff, yoff = 152 * (i % 2), (40 * i // 2)
            text = passive.get_short_desc()
            sprite = SimpleSprite(passive.image_name)
            sprite.rect.x, sprite.rect.y = (self.basex + xoff, self.basey + 20 + yoff)
            self.subsprites.append(sprite)
            text_sprite = TextSprite(text, '#ffffff', self.basex + 38 + xoff, self.basey + 24 + yoff)
            self.subsprites.append(text_sprite)
            if sprite.rect.collidepoint(mouse_pos):
                self.tooltip.set_text("%s\n%s" % (passive.name, passive.get_description()))
                if self.tooltip not in self.subsprites:
                    self.subsprites.append(self.tooltip)
            elif self.tooltip in self.subsprites:
                self.subsprites.remove(self.tooltip)


class LogDisplay (CascadeElement):
    def __init__ (self):
        super().__init__(self)
        self.lines = ["", "", "", ""]
        self.line_sprites = [
                TextSprite('', '#999999', 354, 16),
                TextSprite('', '#999999', 354, 32),
                TextSprite('', '#999999', 354, 48),
                TextSprite('', '#ffffff', 354, 64),
            ]
        self.subsprites = self.line_sprites

    def push_text(self, text):
        self.lines.append(text)
        for line, sprite in zip(self.lines[-4:], self.line_sprites):
            sprite.set_text(line)


class DamageLogDisplay (CascadeElement):
    def __init__(self):
        super().__init__(self)
        self.lines = [(None, None, 0)] * 5
        self.number_sprites = [ TextSprite('', '#ffffff', 848, 138 + 32 * i) for i in range(5) ]
        self.author_sprites = [
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
            SimpleSprite('tiles/Skeleton.png'),
        ]
        self.mean_sprites = [
            SimpleSprite('icons/sword.png'),
            SimpleSprite('icons/sword.png'),
            SimpleSprite('icons/sword.png'),
            SimpleSprite('icons/sword.png'),
            SimpleSprite('icons/sword.png'),
        ]
        self.basex, self.basey = 780, 132
        for i in range(5):
            self.author_sprites[i].rect.x = self.basex
            self.author_sprites[i].rect.y = self.basey + 32 * i
            self.mean_sprites[i].rect.x = self.basex + 32
            self.mean_sprites[i].rect.y = self.basey + 32 * i
        self.subsprites = []

    def update(self):
        self.subsprites = []
        for i, line in enumerate(self.lines):
            if line[0]:
                self.author_sprites[i].animate(line[0])
                self.subsprites.append(self.author_sprites[i])
            if line[1]:
                self.mean_sprites[i].animate(line[1])
                self.subsprites.append(self.mean_sprites[i])
            if line[2]:
                self.number_sprites[i].set_text(str(line[2]))
                self.subsprites.append(self.number_sprites[i])
        self.display()

    def push_line(self, image1, image2, number):
        self.lines.append((image1, image2, number))
        self.lines.pop(0)


class NextToActDisplay (CascadeElement):
    def __init__(self):
        super().__init__(self)
        self.subsprites = []
        self.basex, self.basey = 904, 92

    def update(self, combat):
        to_act = sorted(combat.creatures.values(), key= lambda x: x.next_action) * 2
        self.subsprites = []
        for actor in to_act[:14]:
            self.subsprites.append(SimpleSprite(actor.image_name))
        for i in range(len(self.subsprites)):
            self.subsprites[i].rect.x = self.basex
            self.subsprites[i].rect.y = self.basey + 32 * i


class StepHint(CascadeElement):
    def __init__(self):
        super().__init__()
        self.subsprites = [TextSprite('[%d]' % (i + 4), '#00FF00', 0, 0) for i in range(6)]
        for text in self.subsprites:
            for sprite in text.textsprites:
                sprite.image.set_alpha(120)

    def update(self, creature):
        if not creature.is_pc:
            self.must_show = False
            return
        self.must_show = True
        for i, neighbour in enumerate(creature.tile.neighbours()):
            if not neighbour.in_boundaries(creature.combat.MAP_RADIUS) or neighbour in creature.combat.creatures:
                self.subsprites[i].must_show = False
                continue
            x, y = neighbour.display_location()
            self.subsprites[i].textsprites[0].rect.x, self.subsprites[i].textsprites[0].rect.y = x + 4, y + 6
            self.subsprites[i].must_show = True


class HoverXair(SimpleSprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tile = None

    def display(self):
        if not self.tile:
            return
        self.rect.x, self.rect.y = self.tile.display_location()
        super().display()

    def update(self, tile):
        self.tile = tile


class HelpInterface(Interface, CascadeElement):
    def __init__(self, father):
        CascadeElement.__init__(self)
        Interface.__init__(self,father, keys = [
            (K_ESCAPE, self.cancel),
            ])
        t = Tooltip()
        t.set_text("""Use special abilities with numpad [1-3], confirm target with mouse click or [1-9].
Press [0] to idle for half a turn.
Press [Esc] to cancel or quit.""")
        self.subsprites = [t]
        self.display()

    def cancel(self, key):
        self.done()


class Tooltip(CascadeElement):
    def __init__(self):
        super().__init__()
        self.basex, self.basey = 274, 220
        self.bg = SimpleSprite('helpmodal.png')
        self.bg.rect.move_ip(self.basex, self.basey)
        self.subsprites = [self.bg]

    def set_text(self, text):
        self.subsprites = [self.bg]
        for i, line in enumerate(text.split('\n')):
            t = TextSprite(line, '#ffffff', maxlen=350, x=self.basex + 20, y=self.basey + 20 + 50 * i)
            self.subsprites.append(t)


class TargetInterface(Interface):
    def __init__(self, father, valid_targets, ability):
        super().__init__(father, keys=[
            (K_ESCAPE, self.cancel),
            ('[0-9]', self.choose),
            ])
        self.target = self.father.combat.selected if self.father.combat.selected \
            and self.father.combat.selected in valid_targets else valid_targets[0]
        self.valid_targets = valid_targets
        self.ability = ability
        self.father.combat_ui.cursor.animate('icons/target-cursor.png')
        self.updates = 0

    def cancel(self, key):
        self.target = None
        self.father.combat.selected = None
        self.done()

    def choose(self, key):
        if int(key) > len(self.valid_targets):
            return
        if int(key) == 0 and len(self.valid_targets) > 9:
            self.valid_targets = self.valid_targets[9:] + self.valid_targets[:9]
            return
        self.target = self.valid_targets[int(key) - 1]
        if self.updates > 3:
            self.confirm()

    def update(self, mouse_pos):
        self.updates += 1
        self.father.combat_ui.update(self.father.combat, mouse_pos)
        range_hint = self.father.combat.get_range_hint(self.father.combat.to_act, self.ability)
        for target in range_hint:
            self.father.combat_ui.arena.board[target].animate('tiles/GreyTile2.png')
        splash_hint = self.father.combat.get_splash_hint(self.father.combat.to_act, self.ability, self.target)
        for target in splash_hint:
            self.father.combat_ui.arena.board[target].animate('tiles/Yellow2.png')
        targets_hint = []
        backgrounds = []
        for i, target in enumerate(self.valid_targets):
            key = i + 1 if i < 9 else 0
            x, y = target.display_location()
            t = TextSprite('[%d]' % key, '#ffff00', x=x + 4, y=y + 6)
            background = Gauge(32, 32, '#000000')
            background.move_to(x, y)
            background.image.set_alpha(50)
            backgrounds.append(background)
            targets_hint.append(t)
        tile = GameTile.get_tile_for_mouse(mouse_pos)
        if tile and tile in self.valid_targets:
            self.target = tile
        self.father.combat_ui.display()
        for t in backgrounds:
            t.display()
        for t in targets_hint:
            t.display()
        self.father.combat_ui.cursor.display()

    def on_click(self, mouse_pos):
        self.target = GameTile.get_tile_for_mouse(mouse_pos)
        if self.target and self.target in self.valid_targets:
            self.father.combat.selected = None
            self.done()

    def confirm(self):
        self.father.combat.selected = None
        self.done()


class QuitInterface(Interface, CascadeElement):
    def __init__(self, father):
        CascadeElement.__init__(self)
        Interface.__init__(self, father, keys=[
            (K_ESCAPE, self.cancel),
            ('y', self.confirm),
            ('n', self.cancel),
        ])
        text = 'Really quit ? [y] / [n]'
        basex, basey = 274, 220
        bg = SimpleSprite('helpmodal.png')
        bg.rect.move_ip(basex, basey)
        t1 = TextSprite(text, '#ffffff', maxlen=350, x=basex + 20, y=basey + 100)
        self.subsprites = [bg, t1]
        self.display()

    def cancel(self, key):
        self.done()

    def confirm(self, key):
        exit(0)


class GameUI(CascadeElement):
    def __init__(self, combat):
        super().__init__()
        self.arena = Arena(combat.MAP_RADIUS)
        self.cursor = SimpleSprite('icons/magnifyingglass.png')
        self.hover_display = InfoDisplay(18, 90)
        self.log_display = LogDisplay()
        self.bg = SimpleSprite('bg.png')
        self.dmg_log_display = DamageLogDisplay()
        self.to_act_display = NextToActDisplay()
        self.hover_xair = HoverXair('icons/target.png')
        self.hover_xair.rect.x, self.hover_xair.rect.y = GameTile(0, 0).display_location()
        self.selected_xair = HoverXair('icons/select.png')
        self.subsprites = [self.bg, self.arena, self.log_display, self.dmg_log_display, self.to_act_display,
                           self.hover_display, self.hover_xair, self.selected_xair, self.cursor]
        for c in combat.creatures.values():
            self.subsprites.insert(3, c)
        self.log_display.push_text('Press [?] for help and keybindings')
        self.game_frame = 0

    def update(self, combat, mouse_pos):
        self.game_frame += 1
        self.cursor.rect.x, self.cursor.rect.y = mouse_pos[0] - 10, mouse_pos[1] - 10
        tile = GameTile.get_tile_for_mouse(mouse_pos)
        self.hover_xair.update(tile)
        self.selected_xair.update(combat.selected)
        for creature in combat.creatures.values():
            if creature not in self.subsprites:
                self.subsprites.insert(3, creature)
        creature = combat.creatures.get(tile, combat.creatures.get(combat.selected, combat.to_act))
        if creature:
            self.hover_display.update(creature, mouse_pos)
            self.hover_display.must_show = True
        else:
            self.hover_display.must_show = False
        self.arena.update(combat.to_act)


