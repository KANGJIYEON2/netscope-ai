from datetime import datetime


class Log:
    def __init__(
        self,
        source: str,
        message: str,
        level: str,
        timestamp: datetime,
        received_at: datetime,
    ):
        self.source = source
        self.message = message
        self.level = level
        self.timestamp = timestamp
        self.received_at = received_at
