from datetime import datetime, UTC


class Log:
    def __init__(
        self,
        source: str,
        message: str,
        level: str,
        timestamp: datetime | None = None,
        received_at: datetime | None = None,
    ):
        # timestamp/received_at are optional so lightweight callers (validation
        # fixtures, ad-hoc analysis) don't have to fabricate them. Time-based
        # rules (R019-R024) sort/subtract on `.timestamp`, so it must never be
        # None — fall back to received_at, then to now().
        if received_at is None:
            received_at = datetime.now(UTC)
        if timestamp is None:
            timestamp = received_at
        self.source = source
        self.message = message
        self.level = level
        self.timestamp = timestamp
        self.received_at = received_at
