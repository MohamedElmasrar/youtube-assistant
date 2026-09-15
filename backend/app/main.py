"""Custom routes for the LangGraph Agent Server (`http.app` in langgraph.json).

Threads, runs, streaming and checkpoints are served by the Agent Server itself; this app only
adds video endpoints and mounts the MCP server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.videos import router as videos_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.mcp.youtube_server import mcp

logger = logging.getLogger(__name__)

# FastMCP builds its Starlette app lazily; creating it first also creates the session manager
# whose lifespan must run for the mounted app to serve requests.
mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="YouTube Assistant API", lifespan=lifespan)
app.include_router(videos_router)
app.mount(get_settings().mcp_mount_path, mcp_app)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}}
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "invalid_request", "message": "The request is not valid."}},
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "Something went wrong."}},
    )
