import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from memexia_backend.routers import (
    graph_router,
    nodes_router,
    auth_router,
    knowledge_bases_router,
    users_router,
    admin_router,
)
from memexia_backend.database import close_connections
from memexia_backend.database import engine, Base
from memexia_backend.services.init_service import init_all_services

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create SQL database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown tasks."""
    # Startup
    logger.info("🚀 Starting Memexia Backend...")

    # Initialize all services including Neo4j deployment
    try:
        init_all_services()
    except SystemExit:
        # Allow graceful exit if initialization fails
        logger.error("❌ Service initialization failed, exiting...")
        yield
        return
    except Exception as e:
        logger.error(f"❌ Unexpected error during initialization: {e}")
        yield
        return

    logger.info("✅ Memexia Backend started successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Memexia Backend...")
    close_connections()
    logger.info("✅ Memexia Backend shutdown complete")


app = FastAPI(
    title="Memexia Backend",
    description="API for Memexia - Autonomous Thought Universe",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(graph_router)
app.include_router(nodes_router)
app.include_router(knowledge_bases_router)
app.include_router(users_router)
app.include_router(admin_router)


@app.get("/")
def read_root():
    """Root endpoint - health check."""
    return {"message": "Welcome to Memexia API", "status": "healthy"}
