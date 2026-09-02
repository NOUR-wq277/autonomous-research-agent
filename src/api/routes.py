"""FastAPI application providing REST endpoints for the Autonomous Research Agent."""

import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
        """Execute end-to-end autonomous research on a user topic."""
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

    return app


# Default app instance for uvicorn
app = create_app()
