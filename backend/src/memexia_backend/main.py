from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from memexia_backend.routers import graph_router, nodes_router, auth_router
from memexia_backend.database import close_connections
from memexia_backend.database import engine, Base

# Create SQL database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        close_connections()


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

# Lifespan handler ensures connections are closed on shutdown.

@app.get("/")
def read_root():
    return {"message": "Welcome to Memexia API"}
