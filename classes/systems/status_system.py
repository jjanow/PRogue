from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.entity import Entity


class StatusSystem:
    def update(self, entity: Entity, messages: list[str]) -> None:
        boosts = entity.status_comp.boosts
        for stat, boost in list(boosts.items()):
            boost['duration'] -= 1
            if boost['duration'] <= 0:
                del boosts[stat]
                messages.append(f"Your {stat.capitalize()} boost wears off.")
