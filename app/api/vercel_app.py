"""Resilient Vercel FastAPI entrypoint that surfaces import tracebacks instead of opaque 500s."""
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from app.api.main import app  # noqa: F401
except Exception:
    _err = traceback.format_exc()
    app = FastAPI(title="AI Stock Analyzer (Boot Diagnostic)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    def boot_diagnostic(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={"status": "boot_error", "path": path, "traceback": _err},
        )
