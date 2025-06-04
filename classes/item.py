class Item:
    def __init__(self, name, effect, duration=None, value=None, weight=1, effect_type=None, gold_value=0, material_type=None):
        self.name = name
        self.effect = effect
        self.duration = duration
        self.value = value
        self.weight = weight
        self.effect_type = effect_type
        self.gold_value = gold_value
        self.material_type = material_type
        self.x = None
        self.y = None
        self.quantity = 1
        # Track whether the player has seen this item on the ground. Items should
        # only be visible outside the current field of view after they have been
        # discovered once.
        self.seen = False

    def __eq__(self, other):
        if isinstance(other, Item):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

class Equipment(Item):
    def __init__(self, name, slot, body_part, stat_boost, damage=None, ac=None, accuracy_bonus=0, weight=1, material_type=None, gold_value=0):
        super().__init__(name, None, None, None, weight, None, gold_value)
        self.slot = slot
        self.body_part = body_part
        self.damage = damage
        self.ac = ac if ac is not None else 0
        self.stat_boost = stat_boost

        # Separate bonuses allow items to affect different stats
        if slot in ['weapon', 'missile weapon']:
            self.damage_bonus = stat_boost
            self.defense_bonus = 0
        else:
            self.damage_bonus = 0
            self.defense_bonus = stat_boost

        self.accuracy_bonus = accuracy_bonus
        self.material_type = material_type
