from fastapi import FastAPI

app = FastAPI(
    title="ToolRegistry-Hub OpenAPI Server",
    description="An API for accessing various tools like calculators, unit converters, and web search engines.",
    version="0.3.0",
)

