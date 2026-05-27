"""Error types for the MythicMCP plugin system."""


class AgentNotFoundError(ValueError):
    """Raised when an agent name is not found in the plugin registry."""


class AgentAlreadyLoadedError(ValueError):
    """Raised when attempting to load an agent whose tools are already registered."""


class AgentNotLoadedError(ValueError):
    """Raised when attempting to unload an agent whose tools are not registered."""
