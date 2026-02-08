from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import shutil
from pathlib import Path

router = APIRouter(prefix="/upload", tags=["Upload"])

# Create upload directories
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PRODUCTS_DIR = UPLOAD_DIR / "products"
PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non autorisé. Extensions autorisées: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Taille maximale: 5MB"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Return the URL
    return {
        "filename": unique_filename,
        "url": f"/api/upload/images/{unique_filename}",
        "size": len(content)
    }


@router.get("/images/{filename}")
async def get_image(filename: str):
    """Serve an uploaded image"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image non trouvée")
    
    # Determine content type
    ext = Path(filename).suffix.lower()
    content_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    
    return FileResponse(
        path=file_path,
        media_type=content_types.get(ext, "application/octet-stream")
    )


@router.delete("/images/{filename}")
async def delete_image(filename: str):
    """Delete an uploaded image"""
    file_path = UPLOAD_DIR / filename
    
    if file_path.exists():
        os.remove(file_path)
        return {"message": "Image supprimée"}
    
    return {"message": "Image non trouvée"}


@router.get("/products/{filename}")
async def get_product_image(filename: str):
    """Serve a product image"""
    file_path = PRODUCTS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image non trouvée")
    
    # Determine content type
    ext = Path(filename).suffix.lower()
    content_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    
    return FileResponse(
        path=file_path,
        media_type=content_types.get(ext, "application/octet-stream"),
        headers={"Cache-Control": "public, max-age=31536000"}  # 1 year cache
    )
