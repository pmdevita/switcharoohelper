import json

class LastData:
    """Saves the last time checked and last submission id for checking the next roo"""
    def __init__(self, path=None):
        self.path = "last_data.json"
        if path:
            self.path = path

        try:
            with open(self.path, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

    def get(self, *args, **kwargs):
        return self.data.get(*args, **kwargs)

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f)
