import logging.config
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.utils.constants as const
from app.exceptions.handlers import register_exception_handlers
from app.middleware import LoggingMiddleware
from app.routers.tasks import router as tasks_router

# Logs directory
os.makedirs(const.LOGS_DIR, exist_ok=True)

# Logging config
logging.config.fileConfig(
    const.LOGGING_CONFIG_FILE,
    defaults={"logdir": const.LOGS_DIR},
    disable_existing_loggers=False,
)

logger = logging.getLogger("task_approval")


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info("Starting up Task Approval Workflow API")
    yield
    logger.info("Shutting down Task Approval Workflow API")


app = FastAPI(title="Task Approval Workflow API", lifespan=lifespan)

app.add_middleware(LoggingMiddleware)

register_exception_handlers(app)
app.include_router(tasks_router)
