import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import get_current_admin
from app.models.admin_user import AdminUser
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/admin/upload", tags=["admin-upload"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class UploadResponse(BaseModel):
    url: str
    filename: str
    size_bytes: int


@router.post("", response_model=ApiResponse[UploadResponse])
async def upload_product_image(
    file: UploadFile = File(...),
    current_admin: AdminUser = Depends(get_current_admin),
) -> ApiResponse[UploadResponse]:
    """Upload local product image file and save under backend/data/uploads/products/."""
    # 1. Validate file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: PNG, JPG, JPEG, WEBP",
        )

    # 2. Read contents and check size
    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size ({file_size / (1024 * 1024):.1f}MB) exceeds the 5MB limit",
        )

    # 3. Create destination directory
    products_dir = settings.STATIC_UPLOADS_DIR / "products"
    products_dir.mkdir(parents=True, exist_ok=True)

    # 4. Generate unique, safe filename
    unique_name = f"{uuid.uuid4().hex[:12]}_{Path(file.filename or 'image').stem[:30]}{file_ext}"
    dest_path = products_dir / unique_name

    # 5. Write to local disk
    with open(dest_path, "wb") as f:
        f.write(contents)

    # 6. Relative public URL served via FastAPI StaticFiles
    relative_url = f"/static/uploads/products/{unique_name}"

    return ApiResponse(
        success=True,
        data=UploadResponse(
            url=relative_url,
            filename=unique_name,
            size_bytes=file_size,
        ),
    )
