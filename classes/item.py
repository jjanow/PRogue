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
        self.x: int | None = None
        self.y: int | None = None
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
    
    def to_dict(self):
        """Convert item to dictionary for serialization."""
        return {
            'name': self.name,
            'effect': self.effect.__name__ if self.effect else None,
            'duration': self.duration,
            'value': self.value,
            'weight': self.weight,
            'effect_type': self.effect_type,
            'gold_value': self.gold_value,
            'material_type': self.material_type,
            'x': self.x,
            'y': self.y,
            'quantity': self.quantity,
            'seen': self.seen
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create item from dictionary."""
        # Import effect functions dynamically
        if data.get('effect'):
            from classes.item_loader import get_effect_function
            effect = get_effect_function(data['effect'])
        else:
            effect = None
            
        item = cls(
            name=data['name'],
            effect=effect,
            duration=data.get('duration'),
            value=data.get('value'),
            weight=data.get('weight', 1),
            effect_type=data.get('effect_type'),
            gold_value=data.get('gold_value', 0),
            material_type=data.get('material_type')
        )
        item.x = data.get('x')
        item.y = data.get('y')
        item.quantity = data.get('quantity', 1)
        item.seen = data.get('seen', False)
        return item

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
    
    def to_dict(self):
        """Convert equipment to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            'slot': self.slot,
            'body_part': self.body_part,
            'damage': self.damage,
            'ac': self.ac,
            'stat_boost': self.stat_boost,
            'damage_bonus': self.damage_bonus,
            'defense_bonus': self.defense_bonus,
            'accuracy_bonus': self.accuracy_bonus
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data):
        """Create equipment from dictionary."""
        equipment = cls(
            name=data['name'],
            slot=data['slot'],
            body_part=data['body_part'],
            stat_boost=data['stat_boost'],
            damage=data.get('damage'),
            ac=data.get('ac'),
            accuracy_bonus=data.get('accuracy_bonus', 0),
            weight=data.get('weight', 1),
            material_type=data.get('material_type'),
            gold_value=data.get('gold_value', 0)
        )
        equipment.x = data.get('x')
        equipment.y = data.get('y')
        equipment.quantity = data.get('quantity', 1)
        equipment.seen = data.get('seen', False)
        return equipment
