class World:
    """Simple ECS world managing entities and their components."""

    def __init__(self):
        self._next_entity_id = 1
        self.components = {}

    def create_entity(self):
        entity_id = self._next_entity_id
        self._next_entity_id += 1
        return entity_id

    def add_component(self, entity, component):
        comp_type = type(component)
        self.components.setdefault(comp_type, {})[entity] = component

    def remove_component(self, entity, comp_type):
        comps = self.components.get(comp_type)
        if comps and entity in comps:
            del comps[entity]

    def get_component(self, comp_type):
        return self.components.get(comp_type, {}).items()

    def get_entity_components(self, entity):
        return {t: comps[entity] for t, comps in self.components.items() if entity in comps}
