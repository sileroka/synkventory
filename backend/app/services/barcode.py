"""
Barcode generation service for inventory items.

Generates Code128 (default), EAN-13, and QR codes and stores the image via storage_service.
"""

import io
from typing import Optional

from barcode import Code128, EAN13
from barcode.writer import ImageWriter
import qrcode

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

    def generate_ean13_image_bytes(self, value: str) -> bytes:
        """Generate an EAN-13 barcode image (PNG) as bytes.

        Note: Value must be 12 numeric digits; checksum is computed automatically.
        """
        if not value.isdigit() or len(value) not in (12, 13):
            raise ValueError("EAN-13 value must be 12 or 13 numeric digits")
        buf = io.BytesIO()
        code = EAN13(value[:12], writer=ImageWriter())
        code.write(buf, {
            "module_width": 0.2,
            "module_height": 10.0,
            "font_size": 12,
            "text_distance": 1.0,
            "quiet_zone": 3.0,
        })
        return buf.getvalue()

    def generate_qr_image_bytes(self, value: str) -> bytes:
        """Generate a QR code image (PNG) as bytes."""
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=2)
        qr.add_data(value)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def store_image_and_get_key(self, item_id: str, img_bytes: bytes, kind: str = "code128") -> str:
        """Store barcode image and return storage key."""
        key = f"barcodes/items/{item_id}-{kind}.png"
        storage_service.put_object(key, img_bytes, content_type="image/png")
        return key


barcode_service = BarcodeService()
