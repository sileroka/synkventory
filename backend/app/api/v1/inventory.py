from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.inventory import InventoryItem as InventoryItemModel
from app.schemas.inventory import InventoryItem, InventoryItemCreate, InventoryItemUpdate

router = APIRouter()


@router.get("/", response_model=List[InventoryItem])
def get_inventory_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve inventory items.
    """
    items = db.query(InventoryItemModel).offset(skip).limit(limit).all()
    return items


@router.get("/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    """
    Get a specific inventory item by ID.
    """
    item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=InventoryItem)
def create_inventory_item(item: InventoryItemCreate, db: Session = Depends(get_db)):
    """
    Create a new inventory item.
    """
    # Check if SKU already exists
    existing_item = db.query(InventoryItemModel).filter(InventoryItemModel.sku == item.sku).first()
    if existing_item:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    db_item = InventoryItemModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{item_id}", response_model=InventoryItem)
def update_inventory_item(item_id: int, item: InventoryItemUpdate, db: Session = Depends(get_db)):
    """
    Update an inventory item.
    """
    db_item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete an inventory item.
    """
    db_item = db.query(InventoryItemModel).filter(InventoryItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}
