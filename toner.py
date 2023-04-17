class Toner:
    def __init__(self, color: str, pages_total: int, remaining_percent: int) -> None:
        self.color = color
        self.pages_total = pages_total
        self.remaining_percent = remaining_percent
        self.used_percent = 100 - remaining_percent