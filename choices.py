import random


class FightOption():
    @staticmethod
    def start(world_interface):
        world_interface.mob_list = world_interface.current_answer['mobs']
        world_interface.start_game()
    @staticmethod
    def end(world_interface):
        world_interface.current_question = REWARD
        world_interface.current_answer = None
        world_interface.display_choices()

class LootOption():
    def __init__(self, average_value):
        self.average_value = average_value
    def start(self, world_interface):
        world_interface.party_gold += self.average_value
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

REWARD = {
        'text':'You loot some valuables from the fight.', 
        'choices': [{
                'text': 'Cool', 
                'handler': LootOption(100),
            }
        ],
}
RANDOM_LIST = [
    {
        'text':'You are ambushed !', 
        'choices': [{
                'text': 'Fight', 
                'handler': FightOption,
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
                'handler': FightOption,
                'mobs': [
                    ('Necromancer', (0, -7)),
                    ('Skeleton', (0, -6)),
                    ('Skeleton', (1, -5.5)),
                    ('Skeleton', (-1, -5.5)),
                ],
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

