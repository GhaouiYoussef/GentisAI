class GentisAIError(Exception):
    """Base exception for GentisAI errors."""


class RoutingError(GentisAIError):
    """Raised when routing cannot produce a valid decision."""


class ProviderError(GentisAIError):
    """Raised when an LLM provider fails."""


class ToolExecutionError(GentisAIError):
    """Raised when a tool cannot be executed safely."""


class SessionStoreError(GentisAIError):
    """Raised when a session store cannot load or persist state."""
