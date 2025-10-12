"""Routes module with automatic router discovery."""

import importlib
import pkgutil
from typing import List

from fastapi import APIRouter
from loguru import logger


def discover_routers() -> List[APIRouter]:
    """Automatically discover and import all routers from route modules.

    This function scans the routes package for Python modules and attempts
    to import the 'router' attribute from each module. This allows for
    automatic registration of new route modules without manual configuration.

    Returns:
        List of APIRouter instances found in route modules
    """
    routers = []

    # Get the current package
    package = __package__
    if not package:
        logger.warning("Could not determine package name for route discovery")
        return routers

    # Iterate through all modules in the routes package
    for importer, modname, ispkg in pkgutil.iter_modules(__path__, package + "."):
        # Skip the current module (__init__.py) and non-route modules
        if (
            modname.endswith(".__init__")
            or modname.endswith(".models")
            or modname.endswith(".auth")
        ):
            continue

        try:
            # Import the module
            module = importlib.import_module(modname)

            # Check if the module has a 'router' attribute
            if hasattr(module, "router") and isinstance(module.router, APIRouter):
                routers.append(module.router)
                logger.info(f"Discovered router from {modname}")
            else:
                logger.debug(f"Module {modname} does not have a valid router attribute")

        except ImportError as e:
            logger.warning(f"Failed to import route module {modname}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error importing {modname}: {e}")

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
