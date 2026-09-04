"""FastAPI application providing REST endpoints, SSE streaming, and Web Dashboard."""

import os
from pathlib import Path
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from src.config.settings import get_settings
from src.schemas.report import HealthResponse, ResearchRequest, ResearchResponse
from src.services.research_service import ResearchService
from src.utils.logging import logger


def create_app(service: Optional[ResearchService] = None) -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title="Autonomous Research Agent API",
        description="Production-grade Autonomous Research System powered by Google Gemini and LangGraph.",
        version="1.0.0",
    )

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize research service instance
    research_service = service or ResearchService()

    # Mount static assets directory
    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Middleware to log request duration and status."""
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"HTTP {request.method} {request.url.path} - Status {response.status_code} ({process_time:.2f}ms)"
        )
        return response

    @app.get("/", include_in_schema=False)
    def serve_dashboard():
        """Serve the primary Web Dashboard HTML."""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"status": "ok", "message": "Autonomous Research Agent API is active. Web UI available at /docs."}

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    def health_check():
        """Health check endpoint to verify service and model availability."""
        return HealthResponse(
            status="ok",
            version="1.0.0",
            primary_model=settings.gemini_model,
            available_models=settings.get_all_models(),
        )

    @app.get("/models", tags=["Models"])
    def list_models():
        """List configured primary and fallback Gemini models."""
        return {
            "primary_model": settings.gemini_model,
            "fallback_models": settings.fallback_models,
            "all_models": settings.get_all_models(),
        }

    @app.post("/research", response_model=ResearchResponse, status_code=status.HTTP_200_OK, tags=["Research"])
    def execute_research(request: ResearchRequest):
        """Execute synchronous end-to-end autonomous research on a user topic."""
        try:
            logger.info(f"Received API research request: '{request.question}'")
            response = research_service.run_research(
                question=request.question,
                max_iterations=request.max_iterations,
            )
            return response
        except Exception as e:
            logger.error(f"Error during research execution: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Research agent execution failed: {str(e)}",
            )

    @app.get("/research/stream", tags=["Research"])
    def stream_research_endpoint(
        question: str = Query(..., min_length=5, description="Research topic or question."),
        max_iterations: Optional[int] = Query(None, ge=1, le=5, description="Max research iterations."),
    ):
        """Execute autonomous research with real-time Server-Sent Events (SSE) streaming."""
        logger.info(f"Received API streaming research request: '{question}'")
        return StreamingResponse(
            research_service.stream_research(question=question, max_iterations=max_iterations),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return app


# Default app instance for uvicorn
app = create_app()
