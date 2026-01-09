# Models package - export all models for SQLAlchemy to discover
from app.models.tenant import Tenant, DEFAULT_TENANT_ID
from app.models.user import User, SYSTEM_USER_ID
from app.models.admin_user import AdminUser
from app.models.category import Category
from app.models.category_attribute import CategoryAttribute
from app.models.location import Location
from app.models.inventory import InventoryItem
from app.models.stock_movement import StockMovement, MovementType
from app.models.audit_log import AuditLog, AuditAction, EntityType
from app.models.item_revision import ItemRevision, RevisionType
from app.models.bill_of_material import BillOfMaterial
from app.models.work_order import WorkOrder, WorkOrderStatus, WorkOrderPriority
from app.models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderLineItem,
    PurchaseOrderStatus,
    PurchaseOrderPriority,
)
from app.models.item_lot import ItemLot
from app.models.supplier import Supplier
from app.models.customer import Customer
from app.models.sales_order import (
    SalesOrder,
    SalesOrderLineItem,
    SalesOrderStatus,
    SalesOrderPriority,
)

__all__ = [
    "Tenant",
    "DEFAULT_TENANT_ID",
    "User",
    "SYSTEM_USER_ID",
    "AdminUser",
    "Category",
    "Location",
    "InventoryItem",
    "StockMovement",
    "MovementType",
    "AuditLog",
    "AuditAction",
    "EntityType",
    "CategoryAttribute",
    "ItemRevision",
    "RevisionType",
    "BillOfMaterial",
    "WorkOrder",
    "WorkOrderStatus",
    "WorkOrderPriority",
    "PurchaseOrder",
    "PurchaseOrderLineItem",
    "PurchaseOrderStatus",
    "PurchaseOrderPriority",
    "ItemLot",
    "Supplier",
    "Customer",
    "SalesOrder",
    "SalesOrderLineItem",
    "SalesOrderStatus",
    "SalesOrderPriority",
]
