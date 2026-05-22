class StatusSystem:
    def update(self, entity, messages):
        boosts = entity.status_comp.boosts
        for stat, boost in list(boosts.items()):
            boost['duration'] -= 1
            if boost['duration'] <= 0:
                del boosts[stat]
                messages.append(f"Your {stat.capitalize()} boost wears off.")
