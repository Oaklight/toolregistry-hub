"""Routes module with automatic router discovery."""

import importlib
import pkgutil
from typing import List

from fastapi import APIRouter
from loguru import logger


def discover_routers() -> List[APIRouter]:
    """Automatically discover and import all routers from route modules.

    This function recursively scans the routes package for Python modules and
    attempts to import the 'router' attribute from each module. This allows for
    automatic registration of new route modules without manual configuration.

    Returns:
        List of APIRouter instances found in route modules
    """
    routers = []

    def _discover_in_package(package_name: str, package_path: List[str]):
        """Recursively discover routers in a package."""
        for importer, modname, ispkg in pkgutil.iter_modules(
            package_path, package_name + "."
        ):
            # Skip __init__.py, models, and auth modules
            if (
                modname.endswith(".__init__")
                or modname.endswith(".models")
                or modname.endswith(".auth")
            ):
                continue

            try:
                # Import the module
                module = importlib.import_module(modname)

                # Check if the module has a 'router' attribute and it's not None
                if hasattr(module, "router") and isinstance(module.router, APIRouter):
                    routers.append(module.router)
                    logger.info(f"Discovered router from {modname}")
                elif hasattr(module, "router") and module.router is None:
                    logger.debug(
                        f"Module {modname} has router=None (likely missing configuration)"
                    )
                elif not ispkg:
                    # Only log for non-package modules that don't have routers
                    logger.debug(
                        f"Module {modname} does not have a valid router attribute"
                    )

                # If it's a package, recursively discover in it
                if ispkg and hasattr(module, "__path__"):
                    _discover_in_package(modname, list(module.__path__))

            except ImportError as e:
                logger.warning(f"Failed to import route module {modname}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error importing {modname}: {e}")

    # Get the current package
    package = __package__
    if not package:
        logger.warning("Could not determine package name for route discovery")
        return routers

    # Start discovery from the routes package
    _discover_in_package(package, list(__path__))

    logger.info(f"Discovered {len(routers)} routers total")
    return routers


def get_all_routers() -> List[APIRouter]:
    """Get all available routers.

    Returns:
        List of all discovered APIRouter instances
    """
    return discover_routers()


# Export the discovery function for easy import
__all__ = ["discover_routers", "get_all_routers"]
