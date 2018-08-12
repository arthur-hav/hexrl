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

    def tick(self, creature, time):
        pass

class Bloodlust(Status):
    def status_start(self, creature):
        creature.damage += 8

    def status_end(self, creature):
        creature.damage -= 8

class Root(Status):
    def status_start(self, creature):
        self.old_speed = creature.speed
        self.root_time = 0
        creature.speed = 0

    def status_end(self, creature):
        creature.speed += self.old_speed

    def tick(self, creature, time):
        self.root_time += time
        if self.root_time > 20:
            creature.take_damage(self.root_time // 20)
            self.root_time %= 20 


STATUSES = {
    'Bloodlust': (Bloodlust, ('Bloodlust', 'icons/bloodlust.png')),
    'Root': (Root, ('Root', 'icons/root.png')),
}
