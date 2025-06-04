from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class Equipment:
    """Equipped items by slot."""
    slots: Dict[str, Optional[Any]] = field(default_factory=dict)
