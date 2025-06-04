"""Basic entity component system implementation."""


class Component:
    """Base class for components."""
    pass


class Entity:
    """Container for components."""

    _id_counter = 0

    def __init__(self):
        self.id = Entity._id_counter
        Entity._id_counter += 1
        self.components = {}

    def add_component(self, component):
        """Register a component with this entity."""
        self.components[component.__class__] = component

    def remove_component(self, comp_type):
        """Remove a component from this entity."""
        self.components.pop(comp_type, None)

    def get(self, comp_type):
        """Retrieve a component by type."""
        return self.components.get(comp_type)


class System:
    """Base system class."""

    def update(self, world):
        """Override to implement behavior."""
        raise NotImplementedError


class World:
    """Container for entities and systems."""

    def __init__(self):
        self.entities = []
        self.systems = []

    def add_entity(self, entity):
        self.entities.append(entity)

    def remove_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)

    def add_system(self, system):
        self.systems.append(system)

    def remove_system(self, system):
        if system in self.systems:
            self.systems.remove(system)

    def get_entities_with(self, *comp_types):
        """Return entities that have all specified component types."""
        result = []
        for entity in self.entities:
            if all(ct in entity.components for ct in comp_types):
                result.append(entity)
        return result

    def update(self):
        """Run all systems once."""
        for system in self.systems:
            system.update(self)

    def run(self, iterations=1):
        """Run the update loop a set number of times."""
        for _ in range(iterations):
            self.update()
