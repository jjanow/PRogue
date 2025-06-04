from dataclasses import dataclass
from typing import Optional


@dataclass
class AI:
    """Basic AI behavior component."""
    behavior: str
    target_id: Optional[int] = None
