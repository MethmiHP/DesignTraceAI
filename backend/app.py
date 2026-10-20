from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from coordinator.api import router as coordinator_router
from database.connection import DATABASE_URL


@asynccontextmanager
async def lifespan(app: FastAPI):
    # psycopg requires a normal PostgreSQL URL,
    # not SQLAlchemy's postgresql+psycopg:// format.
    conninfo = DATABASE_URL.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )

    pool = ConnectionPool(
        conninfo=conninfo,
        min_size=1,
        max_size=5,
        open=False,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
        },
    )

    pool.open(wait=True)

    try:
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()

        from coordinator.langgraph_workflow import (
            build_coordinator_graph,
        )

        app.state.coordinator_graph = build_coordinator_graph(
            checkpointer
        )

        print("Coordinator PostgreSQL checkpoints ready.")

        yield

    finally:
        pool.close()


app = FastAPI(
    title="DesignTrace AI",
    description=(
        "Coordinator-Orchestrated Framework for "
        "Software Design Automation"
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "message": "DesignTrace AI Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


app.include_router(coordinator_router)
