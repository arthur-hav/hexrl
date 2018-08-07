import random

def get_question(key):
    if key in NORMAL_CHOICES:
        return NORMAL_CHOICES[key]
    return SPECIAL_CHOICES[key]

class FightOption():
    def __init__(self, reward_value):
        self.reward_value = reward_value
    def start(self, world_interface):
        world_interface.mob_list = world_interface.current_answer['mobs']
        world_interface.start_game()

class LootOption():
    def __init__(self, average_value):
        self.average_value = average_value
    def start(self, world_interface):
        i = self.average_value / 2
        while random.random() > 0.5:
            i += self.average_value / 2 
        world_interface.party_gold += random.randint(i, i + self.average_value / 2)
        world_interface.this_day_question += 1
        world_interface.pick()
    @staticmethod
    def end(world_interface):
        pass

class HealOption():
    def __init__(self, heal_percent):
        self.heal_percent = heal_percent
    def start(self, world_interface):
        for cr in world_interface.pc_list:
            cr.health += 1 + int((cr.maxhealth - cr.health) * self.heal_percent / 100)
            cr.health = min(cr.health, cr.maxhealth)
        world_interface.day += 1
        world_interface.this_day_question = 0
        world_interface.pick()
    @staticmethod
    def end(world_interface):
        pass

class GameOver():
    @staticmethod
    def start(world_interface):
        world_interface.erase_all()
        world_interface.done()
    @staticmethod
    def end(world_interface):
        pass

NORMAL_CHOICES = {
    'gobelin_squad': {
        'text':'You are ambushed by a gobelin squad and must fight for your life.', 
        'choices': [{
                'text': 'Fight', 
                'handler': FightOption(10),
                'mobs': [
                    ('Gobelin', (0, -7)),
                    ('Gobelin', (4, -6)),
                    ('Gobelin', (-4, -6)),
                ],
            }
        ],
    },
    'undead': {
        'text':"You find a pack of undead creatures. They are willing to make you join their army.", 
        'choices': [{
                'text': 'Fight', 
                'handler': FightOption(40),
                'mobs': [
                    ('Necromancer', (0, -7)),
                    ('Skeleton', (0, -6)),
                    ('Skeleton', (1, -5.5)),
                    ('Skeleton', (-1, -5.5)),
                ],
            }
        ],
    },
}
SPECIAL_CHOICES = {
    'rest':{
        'text':"You rest and heal your wounds.", 
            'choices': [{
                    'text': 'OK', 
                    'handler': HealOption(30),
                }
            ],
        },
    'start':{
        'text':"You start your adventure on the quest for the lost amulet of Yendor. Adventurers venture the land in the search for it as the king promised great wealth to whoever carried it back to him. You venture in the Lost lands, known for its great dangers...", 
            'choices': [{
                    'text': 'OK', 
                    'handler': LootOption(100),
                }
            ],
        },
    'gameover':{
        'text':'You are dead...', 
        'choices': [{
                'text': 'Back to menu', 
                'handler': GameOver
            }
        ],
    },
    'loot':{
        'text':'You scavenge valuables from your previous fight.', 
        'choices': [{
                'text': 'Loot', 
                'handler': LootOption(50),
            }
        ],
    }
}
