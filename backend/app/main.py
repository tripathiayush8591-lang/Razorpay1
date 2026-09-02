from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.cors import setup_cors
from app.api.routes.health import router as health_router
from app.api.routes.products import router as products_router
from app.api.routes.admin_auth import router as admin_auth_router
from app.api.routes.admin_products import router as admin_products_router
from app.api.routes.admin_upload import router as admin_upload_router
from app.api.routes.admin_policies import router as admin_policies_router
from app.api.routes.carts import router as carts_router
from app.api.routes.discovery import router as discovery_router
from app.api.routes.agent import router as agent_router
from app.api.routes.payments import router as payments_router
from app.api.routes.orders import router as orders_router
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist on startup as a fallback
    Base.metadata.create_all(bind=engine)
    # Ensure static upload directories exist
    products_upload_dir = settings.STATIC_UPLOADS_DIR / "products"
    products_upload_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Agentic Commerce API",
    version="1.0.0",
    description="Authoritative backend commerce API for Agentic Commerce MVP",
    lifespan=lifespan,
)

# Setup CORS
setup_cors(app)

# Mount local static file serving for uploaded product images
uploads_dir = settings.STATIC_UPLOADS_DIR
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(uploads_dir)), name="static_uploads")

# Include Routers
app.include_router(health_router)
app.include_router(products_router)
app.include_router(admin_auth_router)
app.include_router(admin_products_router)
app.include_router(admin_upload_router)
app.include_router(admin_policies_router)
app.include_router(carts_router)
app.include_router(discovery_router)
app.include_router(agent_router)
app.include_router(payments_router)
app.include_router(orders_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
