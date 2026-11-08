"""Public exception types for h3lib."""


class H3LibError(Exception):
    """Base error for h3lib."""


class MissingDependencyError(H3LibError):
    """Raised when an optional backend dependency is not installed."""


class StoreError(H3LibError):
    """Raised for store backend failures."""


class CacheError(H3LibError):
    """Raised for cache backend failures."""


class ConfigurationError(H3LibError):
    """Raised for invalid client / factory configuration."""


class ExtensionError(H3LibError):
    """Raised when a required DB spatial/H3 extension cannot be enabled."""


class IndexError_(H3LibError):
    """Raised for invalid H3 indexes or index-mode mismatches."""
