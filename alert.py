class Alert:
    def __init__(self, severity: int, code: str, desc: str, uptime: int):
        self.severity = severity
        self.code = code
        self.desc = desc
        self.uptime = uptime