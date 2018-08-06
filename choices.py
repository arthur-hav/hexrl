import random


class FightOption():
    REWARD = {
        'text':'You loot some valuables from the fight.', 
        'choices': [{
                'text': 'Loot'
            }
        ],
    }
    def __init__(self, reward_value):
        self.reward_value = reward_value
    def start(self, world_interface):
        world_interface.mob_list = world_interface.current_answer['mobs']
        world_interface.start_game()
    def end(self, world_interface):
        world_interface.current_question = self.REWARD
        world_interface.current_question['choices'][0]['handler'] = LootOption(self.reward_value)
        world_interface.current_answer = None
        world_interface.display_choices()

class LootOption():
    def __init__(self, average_value):
        self.average_value = average_value
    def start(self, world_interface):
        i = self.average_value / 2
        while random.random() > 0.5:
            i += self.average_value / 2 
        world_interface.party_gold += random.randint(i, i + self.average_value / 2)
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

RANDOM_LIST = [
    {
        'text':'You are ambushed !', 
        'choices': [{
                'text': 'Fight', 
                'handler': FightOption(10),
                'mobs': [
                    ('Gobelin', (0, -6)),
                    ('Gobelin', (6, 0)),
                    ('Gobelin', (-6, 0)),
                ],
            }
        ],
    },
    {
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
    {
        'text':"You rest and heal your wounds.", 
        'choices': [{
                'text': 'OK', 
                'handler': HealOption(30),
            }
        ],
    },
]

GAMEOVER = {
    'text':'You are dead !', 
    'choices': [{
            'text': 'Back to menu', 
            'handler': GameOver
        }
    ],
}

