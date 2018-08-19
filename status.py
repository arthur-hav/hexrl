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

    def get_description(self):
        return "Gains %d damage." % 8


class Root(Status):
    def status_start(self, creature):
        self.root_time = 0
        creature.rooted.append(self)

    def status_end(self, creature):
        creature.rooted.remove(self)

    def tick(self, creature, time):
        self.root_time += time
        if self.root_time >= 100:
            creature.take_damage(4, 'true')
            self.root_time -= 100 

    def get_description(self):
        return "Imobilized for %d turns. Gets small magical damage over time." % self.duration


STATUSES = {
    'Bloodlust': (Bloodlust, ('Bloodlust', 'icons/bloodlust.png')),
    'Root': (Root, ('Root', 'icons/root.png')),
}
