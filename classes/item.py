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
    def __init__(self, name, char, slot, stat_boost, accuracy_bonus=0):
        super().__init__(name, char, None)
        self.slot = slot
        self.stat_boost = stat_boost

        # Separate bonuses allow items to affect different stats
        if slot in ['weapon', 'missile weapon']:
            self.damage_bonus = stat_boost
            self.defense_bonus = 0
        else:
            self.damage_bonus = 0
            self.defense_bonus = stat_boost

        self.accuracy_bonus = accuracy_bonus
