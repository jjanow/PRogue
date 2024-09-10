class Item:
    def __init__(self, name, char, effect, duration=None):
        self.name = name
        self.char = char
        self.effect = effect
        self.duration = duration
        self.x = None
        self.y = None
        self.quantity = 1

    def __eq__(self, other):
        if isinstance(other, Item):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

class Equipment(Item):
    def __init__(self, name, char, slot, stat_boost):
        super().__init__(name, char, None)
        self.slot = slot
        self.stat_boost = stat_boost