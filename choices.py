import defs
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
                    (defs.MOB1, (0, -6)),
                    (defs.MOB1, (0, 6)),
                    (defs.MOB1, (6, 0)),
                    (defs.MOB1, (-6, 0)),
                ],
            }
        ],
    },
    REWARD
]

GAMEOVER = {
    'text':'You are dead !', 
    'choices': [{
            'text': 'Back to menu', 
            'handler': GameOver
        }
    ],
}

