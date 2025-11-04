from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.core.config import get_settings
from app.infrastructure.storage.mongodb import get_mongodb
from app.infrastructure.storage.redis import get_redis
from app.interfaces.dependencies import get_agent_service
from app.interfaces.api.routes import router
from app.infrastructure.logging import setup_logging
from app.interfaces.errors.exception_handlers import register_exception_handlers
from app.infrastructure.models.documents import AgentDocument, SessionDocument, UserDocument
from beanie import init_beanie

# Initialize logging system
setup_logging()
logger = logging.getLogger(__name__)

# Load configuration
settings = get_settings()


# Create lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code executed on startup
    logger.info("Application startup - Manus AI Agent initializing")
    
    # Initialize MongoDB and Beanie
    await get_mongodb().initialize()

    # Initialize Beanie
    await init_beanie(
        database=get_mongodb().client[settings.mongodb_database],
        document_models=[AgentDocument, SessionDocument, UserDocument]
    )
    logger.info("Successfully initialized Beanie")
    
    # Initialize Redis
    await get_redis().initialize()
    
    try:
        yield
    finally:
        # Code executed on shutdown
        logger.info("Application shutdown - Manus AI Agent terminating")
        # Disconnect from MongoDB
        await get_mongodb().shutdown()
        # Disconnect from Redis
        await get_redis().shutdown()


        logger.info("Cleaning up AgentService instance")
        try:
            await asyncio.wait_for(get_agent_service().shutdown(), timeout=30.0)
            logger.info("AgentService shutdown completed successfully")
        except asyncio.TimeoutError:
            logger.warning("AgentService shutdown timed out after 30 seconds")
        except Exception as e:
            logger.error(f"Error during AgentService cleanup: {str(e)}")

app = FastAPI(title="Manus AI Agent", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Register routes
app.include_router(router, prefix="/api/v1")