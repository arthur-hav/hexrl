import defs

RANDOM_LIST = [
    {
        'text':'You are ambushed !', 
        'choices': [{
                'text': 'Fight', 
                'type': 'fight',
                'mobs': [
                    (defs.MOB1, (0, -6)),
                    (defs.MOB1, (0, 6)),
                    (defs.MOB1, (6, 0)),
                    (defs.MOB1, (-6, 0)),
                ]
            }
        ]
    },
]
GAMEOVER = {
    'text':'You are dead !', 
    'choices': [{
            'text': 'Back to menu', 
            'type': 'gameover',
        }
    ]
}

