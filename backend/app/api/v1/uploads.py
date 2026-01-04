"""
Upload API endpoints for handling file uploads.
"""

import logging
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.tenant import get_current_tenant
from app.core.config import settings
from app.models.user import User
from app.models.inventory import InventoryItem as InventoryItemModel
from app.services.storage import storage_service
from app.schemas.response import DataResponse, ResponseMeta

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


def get_response_meta(request: Request) -> ResponseMeta:
    """Create response metadata with request ID."""
    return ResponseMeta(
        timestamp=datetime.utcnow(),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/inventory/{item_id}/image")
async def upload_inventory_image(
    item_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Upload an image for an inventory item.
    
    - Validates file type and size
    - Optimizes the image (resize, compress)
    - Stores in DigitalOcean Spaces
    - Updates the inventory item with the image key
    """
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required")

    # Validate content type
    if file.content_type not in settings.allowed_image_types_list:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_image_types_list)}"
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB"
        )

    # Get the inventory item
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Delete old image if exists
    if item.image_key:
        await storage_service.delete_image(item.image_key)

    # Upload new image
    image_key = await storage_service.upload_image(
        file_content=content,
        filename=file.filename or "image.jpg",
        content_type=file.content_type,
        tenant_id=str(tenant.id),
    )

    if not image_key:
        raise HTTPException(status_code=500, detail="Failed to upload image")

    # Update inventory item
    item.image_key = image_key
    item.updated_by = user.id
    db.commit()
    db.refresh(item)

    # Generate signed URL for immediate use
    signed_url = storage_service.get_signed_url(image_key)

    logger.info(f"Image uploaded for inventory item {item_id}: {image_key}")

    return DataResponse(
        data={
            "imageKey": image_key,
            "imageUrl": signed_url,
        },
        meta=get_response_meta(request),
    )


@router.delete("/inventory/{item_id}/image")
async def delete_inventory_image(
    item_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete an inventory item's image."""
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context required")

    # Get the inventory item
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    if not item.image_key:
        raise HTTPException(status_code=404, detail="Item has no image")

    # Delete from storage
    success = await storage_service.delete_image(item.image_key)
    if not success:
        logger.warning(f"Failed to delete image from storage: {item.image_key}")

    # Clear image key from item
    item.image_key = None
    item.updated_by = user.id
    db.commit()

    logger.info(f"Image deleted for inventory item {item_id}")

    return DataResponse(
        data={"message": "Image deleted successfully"},
        meta=get_response_meta(request),
    )


@router.get("/inventory/{item_id}/image-url")
async def get_inventory_image_url(
    item_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a signed URL for an inventory item's image."""
    # Get the inventory item
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    if not item.image_key:
        raise HTTPException(status_code=404, detail="Item has no image")

    # Generate signed URL
    signed_url = storage_service.get_signed_url(item.image_key)
    if not signed_url:
        raise HTTPException(status_code=500, detail="Failed to generate image URL")

    return DataResponse(
        data={"imageUrl": signed_url},
        meta=get_response_meta(request),
    )
