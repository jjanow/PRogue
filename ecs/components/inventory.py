from dataclasses import dataclass, field
from collections import Counter


@dataclass
class Inventory:
    """Collection of items component."""
    items: Counter = field(default_factory=Counter)
