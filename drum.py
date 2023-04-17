class Drum:
    def __init__(self, color: str, remaining_percent: int):
        self.color = color
        self.remaining_percent = remaining_percent
        self.used_percent = 100 - remaining_percent