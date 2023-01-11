class MockRedditor:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other: 'MockRedditor'):
        return self.name == other.name
