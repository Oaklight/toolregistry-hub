"""Environment requirements decorator for tool classes.

This module provides a decorator to declare required environment variables
for tool classes, enabling automatic validation and disabling of tools
when their required environment variables are not set.
"""


def requires_env(*envs: str):
    """Declare required environment variables for a tool class.

    This decorator attaches a ``_required_envs`` attribute to the class,
    listing the environment variable names that must be set for the tool
    to function properly.

    Args:
        *envs: One or more environment variable names required by the tool.

    Returns:
        A class decorator that sets ``_required_envs`` on the decorated class.

    Example:
        ```python
        @requires_env("MY_API_KEY")
        class MyTool:
            pass
        MyTool._required_envs  # ['MY_API_KEY']
        ```
    """

    def decorator(cls: type) -> type:
        setattr(cls, "_required_envs", list(envs))
        return cls

    return decorator
