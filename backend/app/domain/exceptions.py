class ConflictError(Exception):
    """The requested change conflicts with the current resource state."""


class RateLimitError(Exception):
    """Retry after the configured request window."""
