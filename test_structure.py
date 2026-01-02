#!/usr/bin/env python3
"""
Simple test to verify the API structure without database
"""
import sys
sys.path.insert(0, '/home/runner/work/synkventory/synkventory/backend')

# Test imports
try:
    from app.core.config import settings
    print("✅ Config imports successfully")
    print(f"   Project: {settings.PROJECT_NAME}")
    print(f"   API Path: {settings.API_V1_STR}")
except Exception as e:
    print(f"❌ Config import failed: {e}")
    sys.exit(1)

try:
    from app.schemas.inventory import InventoryItemCreate, InventoryItem
    print("✅ Schemas import successfully")
except Exception as e:
    print(f"❌ Schema import failed: {e}")
    sys.exit(1)

try:
    # Test schema validation
    test_item = InventoryItemCreate(
        name="Test Item",
        sku="TEST-001",
        description="A test inventory item",
        quantity=10,
        unit_price=29.99,
        category="Electronics",
        location="Warehouse A"
    )
    print("✅ Schema validation works")
    print(f"   Created test item: {test_item.name} ({test_item.sku})")
except Exception as e:
    print(f"❌ Schema validation failed: {e}")
    sys.exit(1)

print("\n✅ All backend structure tests passed!")
