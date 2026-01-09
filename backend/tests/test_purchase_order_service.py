"""
Tests for PurchaseOrderService supplier filtering.
"""

import uuid
from sqlalchemy.orm import Session

from app.models.tenant import DEFAULT_TENANT_ID
from app.models.purchase_order import PurchaseOrder
from app.models.supplier import Supplier
from app.services.purchase_order import purchase_order_service


def create_supplier(db: Session, name: str) -> Supplier:
    supplier = Supplier(
        tenant_id=DEFAULT_TENANT_ID,
        name=name,
        is_active=True,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def create_po(
    db: Session,
    po_number: str,
    supplier_id=None,
    supplier_name=None,
) -> PurchaseOrder:
    po = PurchaseOrder(
        tenant_id=DEFAULT_TENANT_ID,
        po_number=po_number,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
    )
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


class TestPurchaseOrderServiceSupplierFilters:
    def test_filter_by_supplier_id(self, db: Session):
        acme = create_supplier(db, name="Acme Corp")
        beta = create_supplier(db, name="Beta LLC")

        # Linked POs
        po1 = create_po(db, po_number="PO-1", supplier_id=acme.id)
        po2 = create_po(db, po_number="PO-2", supplier_id=beta.id)

        # Text-only supplier name
        po3 = create_po(db, po_number="PO-3", supplier_name="Acme Old")

        # Filter by Acme supplier_id should return only PO-1
        pos, total = purchase_order_service.get_purchase_orders(
            db=db,
            supplier_id=acme.id,
        )
        ids = {str(po.id) for po in pos}
        assert total == 1
        assert po1.id.hex in ids or str(po1.id) in ids

    def test_filter_by_supplier_name_matches_linked_and_text(self, db: Session):
        acme = create_supplier(db, name="Acme Corp")
        create_supplier(db, name="Beta LLC")

        po1 = create_po(db, po_number="PO-10", supplier_id=acme.id)
        po2 = create_po(db, po_number="PO-11", supplier_name="Acme Old")
        po3 = create_po(db, po_number="PO-12", supplier_name="Other Vendor")

        pos, total = purchase_order_service.get_purchase_orders(
            db=db,
            supplier_name="Acme",
        )
        po_numbers = {po.po_number for po in pos}
        assert total == 2
        assert "PO-10" in po_numbers
        assert "PO-11" in po_numbers

    def test_filter_by_supplier_name_beta(self, db: Session):
        beta = create_supplier(db, name="Beta LLC")
        create_po(db, po_number="PO-20", supplier_id=beta.id)
        create_po(db, po_number="PO-21", supplier_name="Beta Supplies")
        create_po(db, po_number="PO-22", supplier_name="Gamma Inc")

        pos, total = purchase_order_service.get_purchase_orders(
            db=db,
            supplier_name="Beta",
        )
        po_numbers = {po.po_number for po in pos}
        assert total == 2
        assert "PO-20" in po_numbers
        assert "PO-21" in po_numbers
