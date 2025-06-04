import json
import os

class Race:
    def __init__(self, name, bonuses):
        self.name = name
        self.bonuses = bonuses


def load_races():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    races_path = os.path.join(script_dir, '..', 'data', 'races.json')
    with open(races_path, 'r') as file:
        race_data = json.load(file)

    races = [Race(r['name'], r.get('bonuses', {})) for r in race_data]
    return races


all_races = load_races()
