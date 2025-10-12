from dotenv import load_dotenv
from fastapi import FastAPI
from loguru import logger

from .routes import get_all_routers

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ToolRegistry-Hub OpenAPI Server",
    description="An API for accessing various tools like calculators, unit converters, and web search engines.",
    version="0.3.0",
)

# Automatically discover and include all routers
routers = get_all_routers()
for router in routers:
    app.include_router(router)
    logger.info(f"Included router with prefix: {router.prefix or '/'}")

logger.info(f"FastAPI app initialized with {len(routers)} routers")
