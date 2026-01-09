"""
Barcode generation service for inventory items.

Generates Code128 barcodes (default) and stores the image via storage_service.
"""

import io
from typing import Optional

from barcode import Code128
from barcode.writer import ImageWriter

from app.services.storage import storage_service


class BarcodeService:
    def generate_code128_image_bytes(self, value: str) -> bytes:
        """Generate a Code128 barcode image (PNG) as bytes."""
        buf = io.BytesIO()
        code = Code128(value, writer=ImageWriter())
        code.write(buf, {
            "module_width": 0.2,
            "module_height": 10.0,
            "font_size": 12,
            "text_distance": 1.0,
            "quiet_zone": 3.0,
        })
        return buf.getvalue()

    def store_image_and_get_key(self, item_id: str, img_bytes: bytes) -> str:
        """Store barcode image and return storage key."""
        key = f"barcodes/items/{item_id}.png"
        storage_service.put_object(key, img_bytes, content_type="image/png")
        return key


barcode_service = BarcodeService()
