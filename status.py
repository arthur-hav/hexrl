from display import SimpleSprite

class Status(SimpleSprite):
    def __init__(self, name, image_name):
        super().__init__(image_name)
        self.name = name
        self.image_name = image_name

    def status_start(self, creature):
        pass

    def status_end(self, creature):
        pass

class Bloodlust(Status):
    def status_start(self, creature):
        creature.damage += 8

    def status_end(self, creature):
        creature.damage -= 8

STATUSES = {
    'Bloodlust': (Bloodlust, ('Bloodlust', 'icons/bloodlust.png'))
}
